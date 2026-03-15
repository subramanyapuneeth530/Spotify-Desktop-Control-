@echo off
echo ============================================
echo  Spotify Desktop Control — Setup
echo ============================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download Python 3.11+ from https://python.org
    pause & exit /b 1
)

echo.
echo [1/3] Creating virtual environment...
python -m venv .venv
if errorlevel 1 ( echo ERROR: venv creation failed. & pause & exit /b 1 )

echo [2/3] Installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt --quiet
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )

echo [3/3] Checking for backend/.env...
if not exist backend\.env (
    echo.
    echo  backend\.env not found.
    echo  Copying .env.example to backend\.env ...
    copy .env.example backend\.env >nul
    echo.
    echo  IMPORTANT: Open backend\.env and fill in your Spotify credentials
    echo  before running the app.
)

echo.
echo  Setup complete!
echo  Run the app with:  run.bat
echo  or:  .venv\Scripts\activate  ^&^&  python GUI\app.py
echo.
pause
