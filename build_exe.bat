@echo off
setlocal
cd /d "%~dp0"

if not exist assets mkdir assets
py -3 build_tools\create_icon.py
if errorlevel 1 goto fail

py -3 -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name SteamVR-Autostart-Manager ^
  --icon assets\app_icon.ico ^
  --version-file build_tools\version_info.txt ^
  steamvr_autostart_manager.py
if errorlevel 1 (
:fail
  echo.
  echo PyInstaller is required to build an exe.
  echo Install it with: py -3 -m pip install pyinstaller
  pause
)
