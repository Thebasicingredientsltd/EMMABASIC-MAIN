@echo off
REM Emma Basic CMS launcher (Windows)
cd /d "%~dp0"
echo Installing/updating dependencies...
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
echo.
echo Starting Emma Basic CMS at http://localhost:5000
echo (Keep this window open. Press Ctrl+C to stop.)
echo.
start "" "http://localhost:5000"
python app.py
