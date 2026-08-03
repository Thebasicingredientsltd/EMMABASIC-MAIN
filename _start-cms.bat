@echo off
REM CMS server helper — keep this window open while editing
setlocal
cd /d "%~dp0cms"
if errorlevel 1 (
  echo ERROR: Could not open the cms folder.
  echo Expected: %~dp0cms
  pause
  exit /b 1
)

set "PY="
call "%~dp0_find-python.bat"
if not defined PY (
  echo ERROR: Python not found. Run setup-this-pc.bat first.
  pause
  exit /b 1
)

echo Emma Basic CMS
echo Folder: %CD%
echo Python: %PY%
echo URL:    http://localhost:5000
echo.
echo Installing/updating packages...
"%PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed.
  pause
  exit /b 1
)
echo.
echo Keep this window open. Press Ctrl+C to stop.
echo.
"%PY%" app.py
echo.
echo Server stopped.
pause
endlocal
