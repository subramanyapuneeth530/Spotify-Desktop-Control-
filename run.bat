@echo off
if not exist .venv\Scripts\activate (
    echo ERROR: Virtual environment not found.
    echo Run setup.bat first.
    pause & exit /b 1
)

if not exist backend\.env (
    echo ERROR: backend\.env not found.
    echo Copy .env.example to backend\.env and fill in your Spotify credentials.
    pause & exit /b 1
)

call .venv\Scripts\activate
python GUI\app.py
