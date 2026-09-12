@echo off
REM ---------------------------------------------------------------------------
REM Runs during the unattended Windows install (mounted at C:\OEM by dockur).
REM Goal: make the desktop cheap to redraw, because every frame it repaints is a
REM frame that has to be encoded and pushed through the tunnel to the browser.
REM ---------------------------------------------------------------------------

setlocal

REM --- Power: stop the VM throttling itself ---------------------------------
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>nul
powercfg /change monitor-timeout-ac 0 2>nul
powercfg /change standby-timeout-ac 0 2>nul
powercfg /hibernate off 2>nul

REM --- Visual effects: kill the animation redraw churn ----------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f
reg add "HKCU\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f
reg add "HKCU\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d 1 /f
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v TaskbarAnimations /t REG_DWORD /d 0 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ListviewAlphaSelect /t REG_DWORD /d 0 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ListviewShadow /t REG_DWORD /d 0 /f

REM --- Reduce background chatter --------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f
sc config SysMain start= disabled 2>nul
sc config WSearch start= disabled 2>nul

REM --- Don't blank or lock the session we're streaming -----------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization" /v NoLockScreen /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v InactivityTimeoutSecs /t REG_DWORD /d 0 /f

REM --- Desktop has no physical monitor; don't hunt for one -------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v MaxMonitors /t REG_DWORD /d 2 /f

endlocal
exit /b 0
