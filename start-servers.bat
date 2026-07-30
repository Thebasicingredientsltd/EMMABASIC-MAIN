@echo off
REM ============================================================
REM  Emma Basic - one-click launcher
REM  Starts the website (port 8080) and the CMS (port 5000),
REM  then opens both in your browser. Just double-click this file.
REM ============================================================
setlocal

REM Find Python: use it from PATH, otherwise fall back to the known install location
set "PY=python"
where python >nul 2>nul || set "PY=C:\Users\TBIL_Manager\AppData\Local\Programs\Python\Python313\python.exe"

REM Free ports 8080 and 5000 first, in case old/stuck servers are still holding them
echo Clearing any old servers on ports 8080 and 5000 ...
powershell -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8080,5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul
timeout /t 1 >nul

echo Starting Emma Basic website (http://localhost:8080) ...
start "Emma Basic - Website (8080)" cmd /k "cd /d C:\Website\Emma-Basic-The-Basic-Ingredients\project && %PY% -m http.server 8080"

echo Starting Emma Basic CMS (http://localhost:5000) ...
start "Emma Basic - CMS (5000)" cmd /k "cd /d C:\Website\cms && %PY% app.py"

REM Give the servers a moment to boot, then open both in the browser
timeout /t 3 >nul
start "" "http://localhost:8080/Emma%%20Basic%%20Homepage.html"
start "" "http://localhost:5000"

echo.
echo Both servers are launching in their own windows.
echo Close those windows (or press Ctrl+C in them) to stop the servers.
endlocal
