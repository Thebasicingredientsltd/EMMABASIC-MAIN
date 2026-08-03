@echo off
REM ============================================================
REM  Emma Basic - one-click launcher
REM  Starts the website (port 8080) and the CMS (port 5000),
REM  then opens both in your browser. Just double-click this file.
REM
REM  Works from any PC — paths are relative to this repo folder.
REM ============================================================
setlocal

REM Repo root = folder containing this .bat
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "PROJECT=%ROOT%\Emma-Basic-The-Basic-Ingredients\project"
set "CMS=%ROOT%\cms"

if not exist "%PROJECT%" (
  echo ERROR: Could not find the website folder:
  echo   %PROJECT%
  echo Make sure this file sits in the repo root ^(EMMABASIC-MAIN^).
  pause
  exit /b 1
)
if not exist "%CMS%\app.py" (
  echo ERROR: Could not find the CMS:
  echo   %CMS%\app.py
  echo Run setup-this-pc.bat first, or clone the full repo.
  pause
  exit /b 1
)

REM Find Python: PATH first, then common install locations
set "PY="
where python >nul 2>nul && for /f "delims=" %%I in ('where python') do if not defined PY set "PY=%%I"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY (
  echo ERROR: Python was not found on this PC.
  echo Install Python 3 from https://www.python.org/downloads/
  echo ^(tick "Add python.exe to PATH" during setup^), then run setup-this-pc.bat.
  pause
  exit /b 1
)

REM Free ports 8080 and 5000 first, in case old/stuck servers are still holding them
echo Clearing any old servers on ports 8080 and 5000 ...
powershell -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8080,5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul
timeout /t 1 >nul

echo Starting Emma Basic website (http://localhost:8080) ...
start "Emma Basic - Website (8080)" /D "%PROJECT%" cmd /k ""%PY%" -m http.server 8080"

echo Starting Emma Basic CMS (http://localhost:5000) ...
start "Emma Basic - CMS (5000)" /D "%CMS%" cmd /k ""%PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt && "%PY%" app.py"

REM Give the servers a moment to boot, then open both in the browser
timeout /t 3 >nul
start "" "http://localhost:8080/Emma%%20Basic%%20Homepage.html"
start "" "http://localhost:5000"

echo.
echo Both servers are launching in their own windows.
echo Close those windows (or press Ctrl+C in them) to stop the servers.
endlocal
