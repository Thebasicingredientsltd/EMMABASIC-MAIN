@echo off
REM ============================================================
REM  Emma Basic - one-click launcher
REM  Starts the website (port 8080) and the CMS (port 5000),
REM  then opens both in your browser. Just double-click this file.
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist "%~dp0_start-website.bat" (
  echo ERROR: _start-website.bat is missing from:
  echo   %~dp0
  echo Pull the latest branch / merge PR #3, then try again.
  pause
  exit /b 1
)
if not exist "%~dp0Emma-Basic-The-Basic-Ingredients\project" (
  echo ERROR: Website project folder not found.
  echo Make sure you are in EMMABASIC-MAIN.
  pause
  exit /b 1
)
if not exist "%~dp0cms\app.py" (
  echo ERROR: cms\app.py not found.
  pause
  exit /b 1
)

set "PY="
call "%~dp0_find-python.bat"
if not defined PY (
  echo ERROR: Python was not found on this PC.
  echo Run setup-this-pc.bat first, or install with:
  echo   winget install -e --id Python.Python.3.13
  echo Then close and reopen Command Prompt.
  pause
  exit /b 1
)
echo Using Python: %PY%
"%PY%" --version
echo.

REM Free ports 8080 and 5000 first
echo Clearing any old servers on ports 8080 and 5000 ...
powershell -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8080,5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul
timeout /t 1 >nul

echo Starting website window...
start "Emma Basic - Website (8080)" cmd /k call "%~dp0_start-website.bat"

echo Starting CMS window...
start "Emma Basic - CMS (5000)" cmd /k call "%~dp0_start-cms.bat"

echo Waiting for servers to come up...
set /a "TRIES=0"
:waitloop
set /a "TRIES+=1"
powershell -NoProfile -Command "$ok=$true; foreach ($p in 8080,5000) { $c=Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue; if (-not $c) { $ok=$false } }; if ($ok) { exit 0 } else { exit 1 }" >nul 2>nul
if not errorlevel 1 goto :ready
if %TRIES% GEQ 30 goto :notready
timeout /t 1 >nul
goto :waitloop

:ready
echo Both ports are listening.
start "" "http://localhost:8080/Emma%%20Basic%%20Homepage.html"
start "" "http://localhost:5000"
echo.
echo Look at the two black server windows if anything looks wrong.
echo Close those windows (or press Ctrl+C in them) to stop the servers.
goto :end

:notready
echo.
echo WARNING: Ports 8080 and/or 5000 are still not listening.
echo Look at the two black windows that opened — they show the error.
echo Common fixes:
echo   - Python not installed / not on PATH → run setup-this-pc.bat
echo   - pip/Flask install failed → read the CMS window
echo   - Wrong folder → must be inside EMMABASIC-MAIN
echo.
echo You can also double-click _start-website.bat and _start-cms.bat
echo one at a time to see the full error text.
pause

:end
endlocal
