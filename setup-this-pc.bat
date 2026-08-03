@echo off
REM ============================================================
REM  Emma Basic — set up THIS PC to edit the website
REM  Double-click once on a new computer. Safe to re-run.
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ========================================
echo   Emma Basic — PC setup
echo ========================================
echo.

REM --- 1. Python -----------------------------------------------------------
set "PY="
where python >nul 2>nul && for /f "delims=" %%I in ('where python') do if not defined PY set "PY=%%I"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"

if not defined PY (
  echo [ ] Python — NOT FOUND
  echo.
  echo Install Python 3 from:
  echo   https://www.python.org/downloads/
  echo Important: tick "Add python.exe to PATH", then re-run this script.
  echo.
  start "" "https://www.python.org/downloads/"
  pause
  exit /b 1
)
echo [x] Python — OK  (%PY%)
%PY% --version

REM --- 2. Git --------------------------------------------------------------
where git >nul 2>nul
if errorlevel 1 (
  echo [ ] Git — NOT FOUND
  echo.
  echo Install Git for Windows from:
  echo   https://git-scm.com/download/win
  echo Then re-run this script.
  echo.
  start "" "https://git-scm.com/download/win"
  pause
  exit /b 1
)
echo [x] Git — OK
git --version

REM --- 3. Confirm we are inside the repo -----------------------------------
if not exist "cms\app.py" (
  echo [ ] Repo — cms\app.py missing
  echo This script must run from inside the EMMABASIC-MAIN folder.
  echo If you have not cloned it yet, open PowerShell and run:
  echo.
  echo   git clone https://github.com/Thebasicingredientsltd/EMMABASIC-MAIN.git
  echo   cd EMMABASIC-MAIN
  echo   setup-this-pc.bat
  echo.
  pause
  exit /b 1
)
if not exist "Emma-Basic-The-Basic-Ingredients\project" (
  echo [ ] Repo — website project folder missing
  pause
  exit /b 1
)
echo [x] Repo folders — OK

REM --- 4. CMS dependencies -------------------------------------------------
echo.
echo Installing CMS packages (Flask)...
%PY% -m pip install --disable-pip-version-check -r cms\requirements.txt
if errorlevel 1 (
  echo [ ] CMS packages — FAILED
  pause
  exit /b 1
)
echo [x] CMS packages — OK

REM --- 5. Local edit mode (no secrets needed on disk) ----------------------
REM Ensure we stay on the classic local + Publish workflow unless .env exists.
if not exist "cms\.env" (
  echo Creating cms\.env for local editing...
  (
    echo # Local PC — edit files on disk, then Publish to GitHub
    echo CMS_BACKEND=local
  ) > "cms\.env"
)
echo [x] CMS mode — local (edit on this PC, Publish button pushes to GitHub)

REM --- 6. GitHub access (needed to Publish) --------------------------------
echo.
echo Checking GitHub access...
set "GH_OK=0"

where gh >nul 2>nul
if not errorlevel 1 (
  gh auth status >nul 2>nul
  if not errorlevel 1 (
    set "GH_OK=1"
    echo [x] GitHub CLI — signed in
  ) else (
    echo [ ] GitHub CLI found but not signed in
  )
) else (
  echo [ ] GitHub CLI ^(gh^) — not installed ^(optional but recommended^)
)

if "%GH_OK%"=="0" (
  echo.
  echo To publish edits from this PC you need write access to:
  echo   https://github.com/Thebasicingredientsltd/EMMABASIC-MAIN
  echo.
  echo Recommended — install GitHub CLI and sign in:
  echo   1. Download: https://cli.github.com/
  echo   2. Open a new Command Prompt in this folder and run:
  echo        gh auth login
  echo      Choose: GitHub.com → HTTPS → Login with a web browser
  echo   3. Re-run setup-this-pc.bat to confirm.
  echo.
  echo Or configure Git credentials however you already do for GitHub.
  echo Ask a repo admin to invite this GitHub account as a collaborator
  echo if Publish fails with permission denied.
  echo.
  start "" "https://cli.github.com/"
) else (
  echo.
  echo Testing push access ^(read-only check^)...
  git fetch origin main >nul 2>nul
  if errorlevel 1 (
    echo [ ] Could not fetch from GitHub — check network / login
  ) else (
    echo [x] Can reach GitHub
  )
)

REM --- 7. Done -------------------------------------------------------------
echo.
echo ========================================
echo   Setup finished
echo ========================================
echo.
echo To edit the website on this PC:
echo   1. Double-click  start-servers.bat
echo   2. CMS opens at      http://localhost:5000
echo   3. Preview site at   http://localhost:8080
echo   4. When ready, use Publish to GitHub in the CMS dashboard
echo.
echo Tip: put a shortcut to start-servers.bat on the Desktop.
echo.
pause
endlocal
