# ---------------------------------------------------------------------------
# Run this INSIDE the Windows VM (admin PowerShell) to cut RDP lag.
#
# Everything here targets one thing: how many bytes each frame costs and how
# hard the CPU works to produce it. On a GPU-less VM at the end of a long
# link, that is what you feel.
#
#   irm https://raw.githubusercontent.com/codecutofficial/kali-cloud-lab/main/windows/rdp-tune.ps1 | iex
#
# Then sign out and reconnect. install.bat already applies this to fresh
# installs; this script is for a box that is already running.
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Continue'
$ts = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services'
New-Item -Path $ts -Force | Out-Null

function Set-Reg($path, $name, $value, $type) {
    New-Item -Path $path -Force | Out-Null
    Set-ItemProperty -Path $path -Name $name -Value $value -Type $type
}

Write-Host "`n=== Graphics encoding ===" -ForegroundColor Cyan

# H.264/AVC 444 for the whole session. Video-codes the desktop instead of
# shipping bitmap deltas: far fewer bytes for scrolling, dragging and video,
# which is what a long link punishes hardest.
Set-Reg $ts 'AVC444ModePreferred' 1 'DWord'
Write-Host "  AVC444 preferred            enabled"

# No GPU here, so hardware encode would silently fall back anyway. Left off
# deliberately: on a shared CI core, software H.264 is the cheaper honest path.
Set-Reg $ts 'AVCHardwareEncodePreferred' 0 'DWord'
Write-Host "  hardware encode             off (no GPU — avoids a silent fallback)"

# Cap the frame rate. Each frame is encode CPU + bytes on the wire; 30 is
# indistinguishable from 60 for desktop work and halves both.
Set-Reg $ts 'DWMFRAMEINTERVAL' 33 'DWord'
Write-Host "  frame interval              33ms (~30fps)"

Write-Host "`n=== Bandwidth ===" -ForegroundColor Cyan

# Favour bandwidth over image fidelity — the right trade at ~280ms RTT.
Set-Reg $ts 'VisualExperiencePolicy' 2 'DWord'
Set-Reg $ts 'ImageQuality' 1 'DWord'
Write-Host "  visual experience           optimised for bandwidth"
Write-Host "  image quality               low (fewest bytes per frame)"

Write-Host "`n=== Desktop redraw cost ===" -ForegroundColor Cyan

# Windows 11's transparency/blur is recomputed constantly and re-encoded every
# frame. It is pure cost over a remote link.
Set-Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize' 'EnableTransparency' 0 'DWord'
Set-Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' 'VisualFXSetting' 2 'DWord'
Set-Reg 'HKCU:\Control Panel\Desktop' 'DragFullWindows' '0' 'String'
Set-Reg 'HKCU:\Control Panel\Desktop\WindowMetrics' 'MinAnimate' '0' 'String'
Set-Reg 'HKCU:\Control Panel\Desktop' 'MenuShowDelay' '0' 'String'
Set-Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' 'TaskbarAnimations' 0 'DWord'
Write-Host "  transparency / animations   off"
Write-Host "  drag full windows           off (outline only — one cheap redraw)"

# A plain colour is one flat region to encode; a photo wallpaper is a full
# screen of detail behind every window you move.
Set-Reg 'HKCU:\Control Panel\Desktop' 'Wallpaper' '' 'String'
Set-Reg 'HKCU:\Control Panel\Colors' 'Background' '0 0 0' 'String'
Write-Host "  wallpaper                   solid black"

Write-Host "`n=== Background load ===" -ForegroundColor Cyan
foreach ($svc in 'SysMain','WSearch','DiagTrack') {
    try { Stop-Service $svc -Force -ErrorAction Stop; Set-Service $svc -StartupType Disabled } catch {}
}
Write-Host "  SysMain / WSearch / DiagTrack  stopped"

Write-Host "`n=== Applying ===" -ForegroundColor Cyan
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "  explorer restarted"

Write-Host "`nDone. Sign out and reconnect for the encoder settings to take effect." -ForegroundColor Green
Write-Host "Biggest remaining win is the network path, not this box — see windows/README.md.`n" -ForegroundColor Yellow
