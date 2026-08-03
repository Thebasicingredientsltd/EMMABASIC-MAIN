@echo off
REM Emma Basic CMS launcher (Windows) — works from any PC
setlocal
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && for /f "delims=" %%I in ('where python') do if not defined PY set "PY=%%I"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY (
  echo ERROR: Python not found. Run setup-this-pc.bat from the repo root first.
  pause
  exit /b 1
)

echo Installing/updating dependencies...
"%PY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt
echo.
echo Starting Emma Basic CMS at http://localhost:5000
echo (Keep this window open. Press Ctrl+C to stop.)
echo.
start "" "http://localhost:5000"
"%PY%" app.py
endlocal
