@echo off
REM Website server helper — keep this window open while editing
setlocal
cd /d "%~dp0Emma-Basic-The-Basic-Ingredients\project"
if errorlevel 1 (
  echo ERROR: Could not open the website project folder.
  echo Expected: %~dp0Emma-Basic-The-Basic-Ingredients\project
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

echo Emma Basic website
echo Folder: %CD%
echo Python: %PY%
echo URL:    http://localhost:8080/Emma%%20Basic%%20Homepage.html
echo.
echo Keep this window open. Press Ctrl+C to stop.
echo.
"%PY%" -m http.server 8080
echo.
echo Server stopped.
pause
endlocal
