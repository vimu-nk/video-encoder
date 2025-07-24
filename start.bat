@echo off
REM Simple Video Encoder Startup Script for Windows

echo [%date% %time%] Starting Video Encoder Platform...

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
echo [%date% %time%] Checking dependencies...
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo [%date% %time%] Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the server
echo [%date% %time%] Starting server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

python start_server.py

pause
