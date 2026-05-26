@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 steamvr_autostart_manager.py
) else (
  python steamvr_autostart_manager.py
)
if errorlevel 1 (
  echo.
  echo If Python is not installed, install Python 3 from https://www.python.org/downloads/windows/
  pause
)
