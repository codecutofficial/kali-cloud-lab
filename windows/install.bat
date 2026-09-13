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

REM --- RDP encoding: the biggest lever on a GPU-less VM ----------------------
REM H.264/AVC 444 video-codes the whole desktop instead of shipping bitmap
REM deltas — far fewer bytes for scrolling and dragging, which is what a long
REM link punishes hardest. Hardware encode stays off: there is no GPU, so it
REM would silently fall back anyway.
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v AVC444ModePreferred /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v AVCHardwareEncodePreferred /t REG_DWORD /d 0 /f
REM ~30fps: each frame costs encode CPU and wire bytes, and 30 is
REM indistinguishable from 60 for desktop work.
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v DWMFRAMEINTERVAL /t REG_DWORD /d 33 /f
REM Favour bandwidth over fidelity — the right trade at high latency.
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v VisualExperiencePolicy /t REG_DWORD /d 2 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" /v ImageQuality /t REG_DWORD /d 1 /f

REM --- Windows 11 transparency is recomputed and re-encoded every frame ------
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f
REM A solid colour is one flat region to encode; a photo wallpaper is a full
REM screen of detail behind every window you move.
reg add "HKCU\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d "" /f
reg add "HKCU\Control Panel\Colors" /v Background /t REG_SZ /d "0 0 0" /f
REM Outline-drag is one cheap redraw instead of a full repaint per pixel moved.
reg add "HKCU\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d 0 /f

REM --- One more background service worth stopping ----------------------------
sc config DiagTrack start= disabled 2>nul

REM === FAKE GPU SUPPORT ======================================================
REM The VM has no physical GPU. These settings enable software rendering and
REM hide the Remote Desktop session so games don't refuse to launch.

REM --- Hide RDP session from games -------------------------------------------
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v TSUserEnabled /t REG_DWORD /d 0 /f 2>nul

REM --- DirectX WARP software renderer (built into Windows 10/11) -------------
reg add "HKLM\SOFTWARE\Microsoft\Avalon.Graphics" /v DisableHWAcceleration /t REG_DWORD /d 1 /f 2>nul
reg add "HKLM\SOFTWARE\Wow6432Node\Microsoft\Avalon.Graphics" /v DisableHWAcceleration /t REG_DWORD /d 1 /f 2>nul

REM --- Mesa3D software OpenGL (llvmpipe) -------------------------------------
REM The workflow downloads Mesa to shared storage. Try multiple known paths.
set "MESA64="
set "MESA32="
for %%D in ("\\host.lan\Data" "D:\Data" "D:\" "C:\OEM") do (
    if exist "%%~D\mesa3d\x64\opengl32.dll" set "MESA64=%%~D\mesa3d\x64"
    if exist "%%~D\mesa3d\x86\opengl32.dll" set "MESA32=%%~D\mesa3d\x86"
)

REM 64-bit Mesa → System32
if defined MESA64 (
    takeown /f "%SystemRoot%\System32\opengl32.dll" >nul 2>&1
    icacls "%SystemRoot%\System32\opengl32.dll" /grant Administrators:F >nul 2>&1
    copy /Y "%MESA64%\opengl32.dll"       "%SystemRoot%\System32\" 2>nul
    copy /Y "%MESA64%\libgallium_wgl.dll" "%SystemRoot%\System32\" 2>nul
    copy /Y "%MESA64%\libglapi.dll"       "%SystemRoot%\System32\" 2>nul
    copy /Y "%MESA64%\dxil.dll"           "%SystemRoot%\System32\" 2>nul
    echo Mesa3D x64 installed to System32
) else (
    echo Mesa3D x64 not found
)

REM 32-bit Mesa → SysWOW64 (for 32-bit games like GTA IV)
if defined MESA32 (
    takeown /f "%SystemRoot%\SysWOW64\opengl32.dll" >nul 2>&1
    icacls "%SystemRoot%\SysWOW64\opengl32.dll" /grant Administrators:F >nul 2>&1
    copy /Y "%MESA32%\opengl32.dll"       "%SystemRoot%\SysWOW64\" 2>nul
    copy /Y "%MESA32%\libgallium_wgl.dll" "%SystemRoot%\SysWOW64\" 2>nul
    copy /Y "%MESA32%\libglapi.dll"       "%SystemRoot%\SysWOW64\" 2>nul
    copy /Y "%MESA32%\dxil.dll"           "%SystemRoot%\SysWOW64\" 2>nul
    echo Mesa3D x86 installed to SysWOW64
) else (
    echo Mesa3D x86 not found - 32-bit games use WARP only
)

REM --- Mesa environment variables -------------------------------------------
setx GALLIUM_DRIVER llvmpipe /M 2>nul
setx MESA_GL_VERSION_OVERRIDE 4.5 /M 2>nul

endlocal
exit /b 0
