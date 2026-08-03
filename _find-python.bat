@echo off
REM Sets PY to a real python.exe (skips the Windows Store stub).
REM Call from other .bat files:  call "%~dp0_find-python.bat"

set "PY="

REM Prefer known install locations first (avoids WindowsApps stub)
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set "PY=%LocalAppData%\Programs\Python\Python310\python.exe"
if not defined PY if exist "%ProgramFiles%\Python313\python.exe" set "PY=%ProgramFiles%\Python313\python.exe"
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"

if defined PY goto :eof

REM Fall back to PATH, but skip Microsoft Store aliases
for /f "delims=" %%I in ('where python 2^>nul') do (
  echo %%I | find /I "\WindowsApps\" >nul
  if errorlevel 1 (
    if not defined PY set "PY=%%I"
  )
)

goto :eof
