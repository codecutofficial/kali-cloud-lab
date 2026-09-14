@echo off
REM ---------------------------------------------------------------------------
REM OEM setup script — runs during unattended Windows install (C:\OEM).
REM Does fast registry tweaks + Mesa3D, then writes bootstrap.ps1 to C:\ and
REM launches it in the background. No storage path guessing for the PS1 file.
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

REM --- RDP encoding ----------------------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v AVC444ModePreferred /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v AVCHardwareEncodePreferred /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v DWMFRAMEINTERVAL /t REG_DWORD /d 33 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v VisualExperiencePolicy /t REG_DWORD /d 2 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v ImageQuality /t REG_DWORD /d 1 /f

REM --- Transparency / wallpaper / drag ---------------------------------------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "" /f
reg add "HKCU\Control Panel\Colors" /v Background /t REG_SZ /d "0 0 0" /f
reg add "HKCU\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d 0 /f

REM --- Background services ---------------------------------------------------
sc config DiagTrack start= disabled 2>nul

REM === FAKE GPU SUPPORT ======================================================
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v TSUserEnabled /t REG_DWORD /d 0 /f 2>nul
reg add "HKLM\SOFTWARE\Microsoft\Avalon.Graphics" /v DisableHWAcceleration /t REG_DWORD /d 1 /f 2>nul
reg add "HKLM\SOFTWARE\Wow6432Node\Microsoft\Avalon.Graphics" /v DisableHWAcceleration /t REG_DWORD /d 1 /f 2>nul

REM --- Mesa3D software OpenGL (llvmpipe) — must copy before first login ------
set "MESA64="
set "MESA32="
for %%D in ("\\host.lan\Data" "D:\Data" "D:\" "C:\OEM") do (
    if exist "%%~D\mesa3d\x64\opengl32.dll" set "MESA64=%%~D\mesa3d\x64"
    if exist "%%~D\mesa3d\x86\opengl32.dll" set "MESA32=%%~D\mesa3d\x86"
)

if defined MESA64 (
    takeown /f "%SystemRoot%\System32\opengl32.dll" >nul 2>&1
    icacls "%SystemRoot%\System32\opengl32.dll" /grant Administrators:F >nul 2>&1
    copy /Y "%MESA64%\opengl32.dll"       "%SystemRoot%\System32\" 2>nul
    copy /Y "%MESA64%\libgallium_wgl.dll" "%SystemRoot%\System32\" 2>nul
    copy /Y "%MESA64%\libglapi.dll"       "%SystemRoot%\System32\" 2>nul
    copy /Y "%MESA64%\dxil.dll"           "%SystemRoot%\System32\" 2>nul
    echo Mesa3D x64 installed to System32
)

if defined MESA32 (
    takeown /f "%SystemRoot%\SysWOW64\opengl32.dll" >nul 2>&1
    icacls "%SystemRoot%\SysWOW64\opengl32.dll" /grant Administrators:F >nul 2>&1
    copy /Y "%MESA32%\opengl32.dll"       "%SystemRoot%\SysWOW64\" 2>nul
    copy /Y "%MESA32%\libgallium_wgl.dll" "%SystemRoot%\SysWOW64\" 2>nul
    copy /Y "%MESA32%\libglapi.dll"       "%SystemRoot%\SysWOW64\" 2>nul
    copy /Y "%MESA32%\dxil.dll"           "%SystemRoot%\SysWOW64\" 2>nul
    echo Mesa3D x86 installed to SysWOW64
)

setx GALLIUM_DRIVER llvmpipe /M 2>nul
setx MESA_GL_VERSION_OVERRIDE 4.5 /M 2>nul

REM === SCHEDULE BOOTSTRAP AS A STARTUP TASK ==================================
REM Instead of running bootstrap.ps1 right now (OEM setup may not have network
REM or full services), we register a scheduled task that fires at first logon.
REM The PS1 is on shared storage; copy it locally first.

set "BOOTSTRAP="
for %%D in ("\\host.lan\Data" "D:\Data" "D:\" "C:\OEM") do (
    if exist "%%~D\oem\bootstrap.ps1" set "BOOTSTRAP=%%~D\oem\bootstrap.ps1"
)
if defined BOOTSTRAP (
    copy /Y "%BOOTSTRAP%" "C:\bootstrap.ps1" >nul 2>&1
) else (
    echo bootstrap.ps1 not found on storage, trying C:\OEM direct...
    if exist "C:\OEM\bootstrap.ps1" copy /Y "C:\OEM\bootstrap.ps1" "C:\bootstrap.ps1" >nul 2>&1
)

if exist "C:\bootstrap.ps1" (
    echo Registering bootstrap as startup task...
    schtasks /create /tn "BootstrapSetup" /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\bootstrap.ps1" /sc onlogon /ru SYSTEM /rl highest /f 2>nul
    REM Also try to run it now in case we already have network
    start "" /B powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\bootstrap.ps1"
    echo Bootstrap scheduled and launched.
) else (
    echo ERROR: bootstrap.ps1 not found anywhere!
)

endlocal
exit /b 0
