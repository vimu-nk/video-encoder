@echo off
REM Windows batch script to stop the Video Encoder Platform service

echo Stopping Video Encoder Platform...

REM Try to read PID from file
if exist "logs\service.pid" (
    set /p PID=<logs\service.pid
    echo Attempting to stop service with PID: !PID!
    taskkill /PID !PID! /F >nul 2>&1
    if errorlevel 1 (
        echo Warning: Could not stop process with PID !PID!
    ) else (
        echo Service stopped successfully.
    )
    del logs\service.pid >nul 2>&1
) else (
    echo PID file not found. Attempting to stop all Python processes running service.py...
)

REM Kill all Python processes that might be running our service
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    wmic process where "processid=%%i" get commandline /format:value | findstr service.py >nul 2>&1
    if not errorlevel 1 (
        echo Stopping Python process %%i running service.py
        taskkill /PID %%i /F >nul 2>&1
    )
)

echo.
echo Video Encoder Platform service has been stopped.
echo.
pause
