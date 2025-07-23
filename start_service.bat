@echo off
REM Windows batch script to run the Video Encoder Platform in background

echo Starting Video Encoder Platform...

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt >logs\install.log 2>&1

REM Start the service in background using start command
echo Starting service in background...
start /B python service.py >logs\service_output.log 2>&1

echo.
echo Video Encoder Platform is now running in background!
echo.
echo Dashboard URL: http://localhost:8000
echo Logs location: logs\service_output.log
echo.
echo To stop the service, run: stop_service.bat
echo Or find the process and kill it manually
echo.

REM Create a PID file for easier management (Windows doesn't have direct PID support)
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh ^| findstr service.py') do (
    echo %%i > logs\service.pid
    echo Service PID: %%i
)

echo Press any key to continue...
pause >nul
