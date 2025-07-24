@echo off
REM Video Encoder Platform - Background Startup Script (Windows)
REM This script starts the FastAPI application in the background and manages it

setlocal EnableDelayedExpansion

REM Configuration
set APP_DIR=%~dp0
set LOG_DIR=%APP_DIR%logs
set PID_FILE=%LOG_DIR%\video-encoder.pid
set LOG_FILE=%LOG_DIR%\application.log
set ACCESS_LOG=%LOG_DIR%\access.log
set ERROR_LOG=%LOG_DIR%\error.log

REM Colors for output (Windows doesn't support colors well, but we'll try)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

REM Function to print colored output
:print_status
echo %BLUE%[%date% %time%]%NC% %~1
goto :eof

:print_success
echo %GREEN%[%date% %time%]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[%date% %time%]%NC% %~1
goto :eof

:print_error
echo %RED%[%date% %time%]%NC% %~1
goto :eof

REM Main script logic
if "%1"=="start" goto start_service
if "%1"=="stop" goto stop_service
if "%1"=="restart" goto restart_service
if "%1"=="status" goto get_status
if "%1"=="logs" goto show_logs
if "%1"=="info" goto show_info
if "%1"=="help" goto show_usage
if "%1"=="--help" goto show_usage
if "%1"=="/?" goto show_usage

call :print_error "Invalid command: %1"
echo.
goto show_usage

:start_service
call :print_status "Starting Video Encoder service..."

REM Check if already running
if exist "%PID_FILE%" (
    set /p EXISTING_PID=<"%PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>NUL | find /I "uvicorn" >NUL
    if !ERRORLEVEL! EQU 0 (
        call :print_warning "Service is already running (PID: !EXISTING_PID!)"
        goto get_status
    ) else (
        del "%PID_FILE%" 2>NUL
    )
)

REM Create necessary directories
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%APP_DIR%input" mkdir "%APP_DIR%input"
if not exist "%APP_DIR%output" mkdir "%APP_DIR%output"

REM Change to app directory
cd /d "%APP_DIR%"

REM Check dependencies
call :print_status "Checking dependencies..."
python -c "import fastapi, uvicorn" 2>NUL
if !ERRORLEVEL! NEQ 0 (
    call :print_error "Missing required Python packages. Installing..."
    pip install -r requirements.txt
    if !ERRORLEVEL! NEQ 0 (
        call :print_error "Failed to install dependencies"
        exit /b 1
    )
)

REM Check for GPU and NVENC
call :print_status "Checking hardware capabilities..."
nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits 2>NUL
if !ERRORLEVEL! EQU 0 (
    call :print_success "NVIDIA GPU detected"
) else (
    call :print_warning "nvidia-smi not available, checking NVENC via ffmpeg..."
)

ffmpeg -hide_banner -encoders 2>NUL | findstr nvenc >NUL
if !ERRORLEVEL! EQU 0 (
    for /f %%i in ('ffmpeg -hide_banner -encoders 2^>NUL ^| findstr nvenc ^| find /c /v ""') do set NVENC_COUNT=%%i
    call :print_success "NVENC encoders available: !NVENC_COUNT!"
) else (
    call :print_warning "No NVENC encoders detected - will use CPU encoding"
)

REM Start the service in background
call :print_status "Starting FastAPI application..."

REM Use PowerShell to start the process in background and capture PID
powershell -Command "& {$process = Start-Process -FilePath 'uvicorn' -ArgumentList 'app.main:app --host 0.0.0.0 --port 8000 --workers 1 --access-log --log-level info' -PassThru -RedirectStandardOutput '%LOG_FILE%' -RedirectStandardError '%ERROR_LOG%' -WindowStyle Hidden; $process.Id | Out-File -FilePath '%PID_FILE%' -Encoding ascii}"

REM Wait a moment and check if it started successfully
timeout /t 3 /nobreak >NUL

if exist "%PID_FILE%" (
    set /p NEW_PID=<"%PID_FILE%"
    tasklist /FI "PID eq !NEW_PID!" 2>NUL | find /I "python" >NUL
    if !ERRORLEVEL! EQU 0 (
        call :print_success "Video Encoder started successfully (PID: !NEW_PID!)"
        call :print_status "Application logs: %LOG_FILE%"
        call :print_status "Service available at: http://localhost:8000"
        
        REM Wait for service to be ready
        call :print_status "Waiting for service to be ready..."
        for /l %%i in (1,1,30) do (
            curl -s -f http://localhost:8000/api/status >NUL 2>&1
            if !ERRORLEVEL! EQU 0 (
                call :print_success "Service is ready and responding!"
                goto :eof
            )
            timeout /t 1 /nobreak >NUL
            echo|set /p="."
        )
        echo.
        call :print_warning "Service started but may not be fully ready yet"
    ) else (
        call :print_error "Failed to start Video Encoder"
        if exist "%LOG_FILE%" (
            call :print_error "Last 10 lines of log:"
            powershell -Command "Get-Content '%LOG_FILE%' | Select-Object -Last 10"
        )
        exit /b 1
    )
) else (
    call :print_error "Failed to start Video Encoder - no PID file created"
    exit /b 1
)
goto :eof

:stop_service
call :print_status "Stopping Video Encoder service..."

if not exist "%PID_FILE%" (
    call :print_warning "PID file not found - service may not be running"
    goto :eof
)

set /p SERVICE_PID=<"%PID_FILE%"
tasklist /FI "PID eq %SERVICE_PID%" 2>NUL | find /I "python" >NUL
if !ERRORLEVEL! NEQ 0 (
    call :print_warning "Service is not running (PID %SERVICE_PID% not found)"
    del "%PID_FILE%" 2>NUL
    goto :eof
)

call :print_status "Sending termination signal to PID %SERVICE_PID%..."
taskkill /PID %SERVICE_PID% /T /F >NUL 2>&1

REM Wait for process to terminate
for /l %%i in (1,1,10) do (
    tasklist /FI "PID eq %SERVICE_PID%" 2>NUL | find /I "python" >NUL
    if !ERRORLEVEL! NEQ 0 (
        call :print_success "Video Encoder stopped successfully"
        del "%PID_FILE%" 2>NUL
        goto :eof
    )
    timeout /t 1 /nobreak >NUL
)

call :print_error "Failed to stop Video Encoder (process may still be running)"
exit /b 1

:restart_service
call :print_status "Restarting Video Encoder service..."
call :stop_service
timeout /t 2 /nobreak >NUL
call :start_service
goto :eof

:get_status
if not exist "%PID_FILE%" (
    call :print_error "Video Encoder is not running"
    exit /b 1
)

set /p SERVICE_PID=<"%PID_FILE%"
tasklist /FI "PID eq %SERVICE_PID%" 2>NUL | find /I "python" >NUL
if !ERRORLEVEL! EQU 0 (
    call :print_success "Video Encoder is running (PID: %SERVICE_PID%)"
    
    REM Check if the service is responding
    curl -s -f http://localhost:8000/api/status >NUL 2>&1
    if !ERRORLEVEL! EQU 0 (
        call :print_success "Service is responding to HTTP requests"
    ) else (
        call :print_warning "Service is running but not responding to HTTP requests"
    )
) else (
    call :print_error "Video Encoder is not running (PID %SERVICE_PID% not found)"
    del "%PID_FILE%" 2>NUL
    exit /b 1
)
goto :eof

:show_logs
if not exist "%LOG_FILE%" (
    call :print_error "Log file not found: %LOG_FILE%"
    exit /b 1
)

if "%2"=="-f" (
    call :print_status "Following application logs (Ctrl+C to exit):"
    powershell -Command "Get-Content '%LOG_FILE%' -Wait"
) else (
    call :print_status "Showing last 50 lines of application logs:"
    powershell -Command "Get-Content '%LOG_FILE%' | Select-Object -Last 50"
)
goto :eof

:show_info
call :print_status "=== Video Encoder Service Information ==="
echo.
call :print_status "Configuration:"
echo   App Directory: %APP_DIR%
echo   Log Directory: %LOG_DIR%
echo   PID File: %PID_FILE%
echo   Service URL: http://localhost:8000
echo.

call :print_status "File Status:"
if exist "%APP_DIR%" (
    echo   ✓ App directory exists
) else (
    echo   ✗ App directory missing
)
if exist "%APP_DIR%requirements.txt" (
    echo   ✓ Requirements file found
) else (
    echo   ✗ Requirements file missing
)
if exist "%APP_DIR%app\main.py" (
    echo   ✓ Main application found
) else (
    echo   ✗ Main application missing
)
echo.

call :get_status
goto :eof

:show_usage
echo Usage: %~nx0 {start^|stop^|restart^|status^|logs^|info^|help}
echo.
echo Commands:
echo   start    - Start the Video Encoder service
echo   stop     - Stop the Video Encoder service
echo   restart  - Restart the Video Encoder service
echo   status   - Show service status
echo   logs     - Show application logs (use -f to follow)
echo   info     - Show service information
echo   help     - Show this help message
echo.
echo Examples:
echo   %~nx0 start
echo   %~nx0 logs -f
echo   %~nx0 restart
goto :eof
