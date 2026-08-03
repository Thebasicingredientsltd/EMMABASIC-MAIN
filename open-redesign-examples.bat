@echo off
REM Open the Spec Lab redesign examples from THIS repo (OneDrive path safe)
setlocal
cd /d "%~dp0Emma-Basic-The-Basic-Ingredients\project"
if not exist "redesign-examples\index.html" (
  echo ERROR: redesign-examples not found in:
  echo   %CD%
  echo.
  echo Make sure you are on branch cursor/product-page-redesign-dd8b
  echo   git fetch origin
  echo   git checkout cursor/product-page-redesign-dd8b
  echo   git pull
  pause
  exit /b 1
)

echo Serving THIS folder:
echo   %CD%
echo.
echo Open: http://localhost:8080/redesign-examples/
echo.
echo Keep this window open. Press Ctrl+C to stop.
echo.

REM Prefer a free port attempt - clear 8080 first
powershell -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul
timeout /t 1 >nul

start "" "http://localhost:8080/redesign-examples/"
python -m http.server 8080
if errorlevel 1 (
  echo.
  echo Python failed. Try:
  echo   py -3 -m http.server 8080
  pause
)
endlocal
