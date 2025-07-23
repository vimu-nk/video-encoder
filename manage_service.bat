@echo off
echo ================================================================
echo           Video Encoder Platform - Background Service
echo ================================================================
echo.
echo Choose an option:
echo.
echo 1. Start service in background
echo 2. Stop service
echo 3. Check service status
echo 4. View recent logs
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto status
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto exit
goto invalid

:start
echo Starting service...
powershell -ExecutionPolicy Bypass -File "service_manager.ps1" -Start
pause
goto menu

:stop
echo Stopping service...
powershell -ExecutionPolicy Bypass -File "service_manager.ps1" -Stop
pause
goto menu

:status
echo Checking service status...
powershell -ExecutionPolicy Bypass -File "service_manager.ps1" -Status
pause
goto menu

:logs
echo Showing recent logs...
powershell -ExecutionPolicy Bypass -File "service_manager.ps1" -Logs
pause
goto menu

:invalid
echo Invalid choice. Please try again.
pause
goto menu

:menu
cls
echo ================================================================
echo           Video Encoder Platform - Background Service
echo ================================================================
echo.
echo Choose an option:
echo.
echo 1. Start service in background
echo 2. Stop service
echo 3. Check service status
echo 4. View recent logs
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto status
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto exit
goto invalid

:exit
echo.
echo Thank you for using Video Encoder Platform!
echo.
pause
