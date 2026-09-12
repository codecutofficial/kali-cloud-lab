# Handy tools for the Windows lab box.
# Run inside the desktop session:  powershell -ExecutionPolicy Bypass -File windows\tools.ps1
# Chocolatey is preinstalled on GitHub's windows-latest runner.

$ErrorActionPreference = 'Continue'

$tools = @(
  'firefox',        # browser
  'vscode',         # editor
  '7zip',           # archives
  'notepadplusplus',
  'sysinternals',   # procmon, autoruns, tcpview...
  'wireshark',      # network capture
  'nmap',           # port scanner
  'git',
  'python'
)

foreach ($t in $tools) {
  Write-Host "==> installing $t" -ForegroundColor Cyan
  choco install $t -y --no-progress
}

Write-Host ""
Write-Host "Done. Installed:" -ForegroundColor Green
foreach ($t in $tools) { Write-Host "  - $t" }
