@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade -r requirements.txt
if errorlevel 1 (
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" app.py
