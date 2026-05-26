@echo off
setlocal
cd /d "%~dp0"

if not exist dist\SteamVR-Autostart-Manager.exe (
  call build_exe.bat
  if errorlevel 1 exit /b 1
)

set "ISCC_CMD=ISCC"
where ISCC >nul 2>nul
if errorlevel 1 set "ISCC_CMD=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_CMD%" (
  echo.
  echo Inno Setup is required to build the installer.
  echo Install it with: winget install --id JRSoftware.InnoSetup -e
  pause
  exit /b 1
)

"%ISCC_CMD%" installer\SteamVR-Autostart-Manager.iss
