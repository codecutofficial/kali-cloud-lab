# bootstrap.ps1 — Runs in the background after Windows OEM setup.
# Downloads and silently installs: Python, YouTube bot + TTS, OBS Studio, Google Chrome, Parsec.
# All output logged to C:\bootstrap.log
# Writes credentials to Desktop. Drops marker file + cleans up scheduled task when done.

$ErrorActionPreference = 'Continue'
Start-Transcript -Path 'C:\bootstrap.log' -Append

function Log($msg) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" }

# Prevent duplicate runs
$lockFile = 'C:\bootstrap.running'
if (Test-Path $lockFile) {
    $started = (Get-Item $lockFile).LastWriteTime
    if (((Get-Date) - $started).TotalMinutes -lt 30) {
        Log 'Bootstrap already running (lock file exists). Exiting.'
        Stop-Transcript
        exit 0
    }
}
'running' | Out-File $lockFile -Force

# -------------------------------------------------------------------
# Wait for network (OEM setup may fire before DHCP finishes)
# -------------------------------------------------------------------
Log 'Waiting for network...'
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Test-Connection -ComputerName 'www.google.com' -Count 1 -Quiet -ErrorAction SilentlyContinue
        if ($r) { Log 'Network is up'; break }
    } catch {}
    Start-Sleep -Seconds 3
}

# -------------------------------------------------------------------
# Shared storage paths (dockur mounts /storage at multiple locations)
# -------------------------------------------------------------------
$storageDirs = @('\\host.lan\Data', 'D:\Data', 'D:\', 'C:\OEM')

function Find-Storage($sub) {
    foreach ($d in $storageDirs) {
        $p = Join-Path $d $sub
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Download-File($url, $dest, $name) {
    Log "Downloading $name..."
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            curl.exe -fsSL -o $dest $url 2>$null
            if (Test-Path $dest) {
                $size = (Get-Item $dest).Length
                if ($size -gt 1000) {
                    Log "$name downloaded (${size} bytes)"
                    return $true
                }
            }
        } catch {}
        Log "$name download attempt $attempt failed, retrying in 5s..."
        Start-Sleep -Seconds 5
    }
    Log "$name download FAILED after 3 attempts"
    return $false
}

# -------------------------------------------------------------------
# Save credentials to Desktop + C:\
# -------------------------------------------------------------------
Log 'Writing credentials files...'
$password = '(check workflow run)'
# Search for credentials file across all possible storage paths and filenames
foreach ($fname in @('credentials.txt', '.credentials')) {
    foreach ($d in @('\\host.lan\Data', 'D:\Data', 'D:\', 'C:\OEM', '\\host.lan\Data\oem', 'D:\Data\oem', 'D:\oem', 'E:\', 'E:\Data', 'E:\oem')) {
        $p = Join-Path $d $fname
        if (Test-Path $p) {
            try {
                $pw = (Get-Content $p -Raw).Trim()
                if ($pw.Length -gt 2) { $password = $pw; Log "Password found at $p"; break }
            } catch {}
        }
    }
    if ($password -ne '(check workflow run)') { break }
}

# Fallback: read the password dockur set via Autologon registry key
if ($password -eq '(check workflow run)') {
    try {
        $regPw = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name DefaultPassword -ErrorAction Stop).DefaultPassword
        if ($regPw) { $password = $regPw; Log 'Password found in Winlogon registry' }
    } catch {}
}

$credText = @"
Windows VM Credentials
======================
Username: Docker
Password: $password

Connect via Tailscale RDP: winlab:3389
"@

try {
    $credText | Out-File -FilePath 'C:\credentials.txt' -Encoding UTF8 -Force
    $desktopPath = [Environment]::GetFolderPath('Desktop')
    if (-not $desktopPath) { $desktopPath = "$env:USERPROFILE\Desktop" }
    New-Item -ItemType Directory -Path $desktopPath -Force | Out-Null
    $credText | Out-File -FilePath (Join-Path $desktopPath 'README.txt') -Encoding UTF8 -Force
    Log 'Credentials written'
} catch { Log "Credentials file error: $_" }

# ===================================================================
# 1. PYTHON 3.13 (latest stable)
# ===================================================================
Log 'Installing Python 3.13...'
$pyVer = '3.13.2'
$pyInstaller = "$env:TEMP\python-installer.exe"
$pyOk = Download-File "https://www.python.org/ftp/python/$pyVer/python-$pyVer-amd64.exe" $pyInstaller 'Python'
if ($pyOk) {
    try {
        Start-Process -FilePath $pyInstaller -ArgumentList '/quiet','InstallAllUsers=1','PrependPath=1','Include_pip=1' -Wait -NoNewWindow
        Log 'Python installed'
    } catch { Log "Python install error: $_" }
}

# Find Python — try 3.13 first, fall back to 3.12 or whatever is installed
$pythonExe = $null
foreach ($p in @(
    "C:\Program Files\Python313\python.exe",
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe"
)) {
    if (Test-Path $p) { $pythonExe = $p; break }
}

if (-not $pythonExe) {
    # Last resort — check PATH
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if ($pythonExe) {
    $pyDir = Split-Path $pythonExe
    $env:Path += ";$pyDir;$pyDir\Scripts"
    [Environment]::SetEnvironmentVariable('Path', $env:Path, 'Machine')
    Log "Using Python at: $pythonExe"
    & $pythonExe --version 2>&1 | ForEach-Object { Log $_ }
} else {
    Log 'ERROR: Python not found after install!'
}

# ===================================================================
# 2. YOUTUBE BOT + TTS DEPENDENCIES
# ===================================================================
if ($pythonExe) {
    Log 'Installing Python packages...'
    try {
        & $pythonExe -m pip install --upgrade pip 2>$null
        & $pythonExe -m pip install pytchat pyautogui edge-tts pygame 2>$null
        Log 'pip packages installed'
    } catch { Log "pip error: $_" }
}

$botDest = "$env:USERPROFILE\youtube-bot"
$botFound = $false

# Try shared storage first (multiple possible mount points)
foreach ($d in @('\\host.lan\Data', 'D:\Data', 'D:\', 'C:\OEM', 'E:\', 'E:\Data')) {
    $check = Join-Path $d 'youtube-bot\bot.py'
    if (Test-Path $check) {
        $botDir = Split-Path $check
        New-Item -ItemType Directory -Path $botDest -Force | Out-Null
        Copy-Item -Path "$botDir\*" -Destination $botDest -Force
        Log "YouTube bot copied from $botDir"
        $botFound = $true
        break
    }
}

# Fallback: download from GitHub (repo is public)
if (-not $botFound) {
    Log 'Bot not on storage — downloading from GitHub...'
    New-Item -ItemType Directory -Path $botDest -Force | Out-Null
    $repo = 'https://raw.githubusercontent.com/codecutofficial/kali-cloud-lab/main/youtube-bot'
    foreach ($f in @('bot.py','commands.py','tts.py','requirements.txt')) {
        curl.exe -fsSL -o "$botDest\$f" "$repo/$f" 2>$null
    }
    if (Test-Path "$botDest\bot.py") {
        Log 'YouTube bot downloaded from GitHub'
        $botFound = $true
    } else {
        Log 'YouTube bot download FAILED'
    }
}

# ===================================================================
# 3. OBS STUDIO (silent install)
# ===================================================================
Log 'Installing OBS Studio...'
$obsInstaller = "$env:TEMP\obs-installer.exe"
$obsOk = Download-File 'https://cdn-fastly.obsproject.com/downloads/OBS-Studio-31.0.1-Windows-Installer.exe' $obsInstaller 'OBS Studio'
if ($obsOk) {
    try {
        Start-Process -FilePath $obsInstaller -ArgumentList '/S' -Wait -NoNewWindow
        Log 'OBS Studio installed'
    } catch { Log "OBS install error: $_" }
}

# ===================================================================
# 4. GOOGLE CHROME (latest stable, silent)
# ===================================================================
Log 'Installing Google Chrome...'
$chromeInstaller = "$env:TEMP\chrome-installer.exe"
$chromeOk = Download-File 'https://dl.google.com/chrome/install/latest/chrome_installer.exe' $chromeInstaller 'Chrome'
if ($chromeOk) {
    try {
        Start-Process -FilePath $chromeInstaller -ArgumentList '/silent','/install' -Wait -NoNewWindow
        Log 'Google Chrome installed'
    } catch { Log "Chrome install error: $_" }
}

# ===================================================================
# 5. PARSEC (latest, silent)
# ===================================================================
Log 'Installing Parsec...'
$parsecInstaller = "$env:TEMP\parsec-installer.exe"
$parsecOk = Download-File 'https://builds.parsec.app/package/parsec-windows.exe' $parsecInstaller 'Parsec'
if ($parsecOk) {
    try {
        Start-Process -FilePath $parsecInstaller -ArgumentList '/silent','/S' -Wait -NoNewWindow
        Log 'Parsec installed'
    } catch { Log "Parsec install error: $_" }
}

# ===================================================================
# DONE
# ===================================================================
Log '=== Bootstrap complete ==='

# Drop marker file on shared storage so the workflow can detect completion
foreach ($d in $storageDirs) {
    try {
        if (Test-Path $d) {
            'done' | Out-File -FilePath (Join-Path $d 'bootstrap-done.marker') -Force
            break
        }
    } catch {}
}

# Desktop completion notice
try {
    $desktopPath = [Environment]::GetFolderPath('Desktop')
    if (-not $desktopPath) { $desktopPath = "$env:USERPROFILE\Desktop" }
    $status = @()
    $status += if ($pyOk) { '[OK] Python' } else { '[FAIL] Python' }
    $status += if ($botFound) { '[OK] YouTube Bot + TTS' } else { '[FAIL] YouTube Bot' }
    $status += if ($obsOk) { '[OK] OBS Studio' } else { '[FAIL] OBS Studio' }
    $status += if ($chromeOk) { '[OK] Google Chrome' } else { '[FAIL] Google Chrome' }
    $status += if ($parsecOk) { '[OK] Parsec' } else { '[FAIL] Parsec' }
    @"
SETUP COMPLETE
==============
$($status -join "`n")

YouTube Bot: $env:USERPROFILE\youtube-bot\bot.py
Log: C:\bootstrap.log
"@ | Out-File -FilePath (Join-Path $desktopPath 'SETUP-COMPLETE.txt') -Encoding UTF8 -Force
} catch {}

# Toast notification
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0)
    $txt = $template.GetElementsByTagName('text')
    $txt.Item(0).AppendChild($template.CreateTextNode('Setup Complete - All software installed')) | Out-Null
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Windows VM')
    $notifier.Show([Windows.UI.Notifications.ToastNotification]::new($template))
} catch {}

# Clean up: remove the scheduled task and lock file
try { schtasks /delete /tn 'BootstrapSetup' /f 2>$null } catch {}
Remove-Item $lockFile -Force -ErrorAction SilentlyContinue

Stop-Transcript
