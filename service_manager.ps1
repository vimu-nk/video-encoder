# PowerShell script to run Video Encoder Platform as a background service
param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Logs
)

$ServiceName = "VideoEncoderPlatform"
$ServiceDisplayName = "Video Encoder Platform"
$ServiceDescription = "Web-based video encoding platform using Bunny CDN and FFmpeg"
$WorkingDirectory = $PSScriptRoot
$PythonScript = Join-Path $WorkingDirectory "service.py"
$LogDirectory = Join-Path $WorkingDirectory "logs"
$ServiceLogFile = Join-Path $LogDirectory "service.log"
$PidFile = Join-Path $LogDirectory "service.pid"

# Ensure logs directory exists
if (!(Test-Path $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
}

function Show-Usage {
    Write-Host "Video Encoder Platform Service Manager" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\service_manager.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Start     Start the service in background"
    Write-Host "  -Stop      Stop the service"
    Write-Host "  -Status    Show service status"
    Write-Host "  -Logs      Show recent logs"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\service_manager.ps1 -Start"
    Write-Host "  .\service_manager.ps1 -Stop"
    Write-Host "  .\service_manager.ps1 -Status"
}

function Start-EncoderService {
    Write-Host "Starting Video Encoder Platform..." -ForegroundColor Green
    
    # Check if already running
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            Write-Host "Service is already running with PID: $pid" -ForegroundColor Yellow
            return
        }
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Using: $pythonVersion" -ForegroundColor Cyan
    } catch {
        Write-Error "Python is not installed or not in PATH"
        return
    }
    
    # Check if virtual environment exists and activate it
    $venvPath = Join-Path $WorkingDirectory "venv\Scripts\python.exe"
    if (Test-Path $venvPath) {
        $pythonExe = $venvPath
        Write-Host "Using virtual environment" -ForegroundColor Cyan
    } else {
        $pythonExe = "python"
    }
    
    # Install dependencies
    Write-Host "Installing/updating dependencies..." -ForegroundColor Cyan
    & $pythonExe -m pip install -r requirements.txt | Out-File -FilePath (Join-Path $LogDirectory "install.log") -Append
    
    # Start the service as background job
    $job = Start-Job -ScriptBlock {
        param($pythonExe, $scriptPath, $workingDir)
        Set-Location $workingDir
        & $pythonExe $scriptPath
    } -ArgumentList $pythonExe, $PythonScript, $WorkingDirectory
    
    # Save job information
    $job.Id | Out-File -FilePath $PidFile
    
    Start-Sleep -Seconds 2
    
    if ($job.State -eq "Running") {
        Write-Host "✓ Service started successfully!" -ForegroundColor Green
        Write-Host "  Job ID: $($job.Id)" -ForegroundColor Cyan
        Write-Host "  Dashboard URL: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  Logs: $ServiceLogFile" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Use '.\service_manager.ps1 -Status' to check status" -ForegroundColor Yellow
        Write-Host "Use '.\service_manager.ps1 -Stop' to stop the service" -ForegroundColor Yellow
    } else {
        Write-Error "Failed to start service"
        Remove-Item $PidFile -ErrorAction SilentlyContinue
    }
}

function Stop-EncoderService {
    Write-Host "Stopping Video Encoder Platform..." -ForegroundColor Yellow
    
    if (Test-Path $PidFile) {
        $jobId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($jobId) {
            $job = Get-Job -Id $jobId -ErrorAction SilentlyContinue
            if ($job) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
                Remove-Job -Job $job -ErrorAction SilentlyContinue
                Write-Host "✓ Service stopped successfully!" -ForegroundColor Green
            }
        }
        Remove-Item $PidFile -ErrorAction SilentlyContinue
    }
    
    # Also kill any Python processes running our service
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*service.py*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "Service has been stopped." -ForegroundColor Green
}

function Get-ServiceStatus {
    Write-Host "Video Encoder Platform Status" -ForegroundColor Green
    Write-Host "=============================" -ForegroundColor Green
    
    if (Test-Path $PidFile) {
        $jobId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($jobId) {
            $job = Get-Job -Id $jobId -ErrorAction SilentlyContinue
            if ($job -and $job.State -eq "Running") {
                Write-Host "Status: RUNNING ✓" -ForegroundColor Green
                Write-Host "Job ID: $($job.Id)" -ForegroundColor Cyan
                Write-Host "Started: $($job.PSBeginTime)" -ForegroundColor Cyan
                
                # Test if web server is responding
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -ErrorAction Stop
                    Write-Host "Web Server: RESPONDING ✓" -ForegroundColor Green
                    Write-Host "Dashboard: http://localhost:8000" -ForegroundColor Cyan
                } catch {
                    Write-Host "Web Server: NOT RESPONDING ✗" -ForegroundColor Red
                }
            } else {
                Write-Host "Status: STOPPED ✗" -ForegroundColor Red
                Remove-Item $PidFile -ErrorAction SilentlyContinue
            }
        } else {
            Write-Host "Status: STOPPED ✗" -ForegroundColor Red
        }
    } else {
        Write-Host "Status: STOPPED ✗" -ForegroundColor Red
    }
    
    # Show log file info
    if (Test-Path $ServiceLogFile) {
        $logInfo = Get-Item $ServiceLogFile
        Write-Host "Log File: $ServiceLogFile" -ForegroundColor Cyan
        Write-Host "Log Size: $([math]::Round($logInfo.Length / 1KB, 2)) KB" -ForegroundColor Cyan
        Write-Host "Modified: $($logInfo.LastWriteTime)" -ForegroundColor Cyan
    }
}

function Show-ServiceLogs {
    if (Test-Path $ServiceLogFile) {
        Write-Host "Recent logs from: $ServiceLogFile" -ForegroundColor Green
        Write-Host "=================================" -ForegroundColor Green
        Get-Content $ServiceLogFile -Tail 20
    } else {
        Write-Host "No log file found at: $ServiceLogFile" -ForegroundColor Yellow
    }
}

# Main script logic
if ($Start) {
    Start-EncoderService
} elseif ($Stop) {
    Stop-EncoderService
} elseif ($Status) {
    Get-ServiceStatus
} elseif ($Logs) {
    Show-ServiceLogs
} else {
    Show-Usage
}
