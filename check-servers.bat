@echo off
REM Quick diagnosis when localhost shows "can't be reached"
setlocal
cd /d "%~dp0"
echo.
echo === Emma Basic — server check ===
echo Folder: %CD%
echo.

set "PY="
call "%~dp0_find-python.bat"
if defined PY (
  echo [x] Python: %PY%
  "%PY%" --version
) else (
  echo [ ] Python: NOT FOUND
  echo     Run: winget install -e --id Python.Python.3.13
)

echo.
if exist "cms\app.py" (echo [x] cms\app.py found) else (echo [ ] cms\app.py MISSING)
if exist "Emma-Basic-The-Basic-Ingredients\project" (echo [x] website project found) else (echo [ ] website project MISSING)

echo.
echo Port 8080 (website):
powershell -NoProfile -Command "$c=Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue; if ($c) { '  LISTENING' } else { '  NOT listening — site will say cannot be reached' }"
echo Port 5000 (CMS):
powershell -NoProfile -Command "$c=Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue; if ($c) { '  LISTENING' } else { '  NOT listening — CMS will say cannot be reached' }"

echo.
echo If ports are NOT listening, open these and read any red/error text:
echo   _start-website.bat
echo   _start-cms.bat
echo.
pause
endlocal
