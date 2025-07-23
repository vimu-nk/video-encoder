# Running Video Encoder Platform as Background Service

This guide shows you how to run the Video Encoder Platform in the background so it continues running even after you close the terminal.

## Quick Start (Windows)

### Option 1: PowerShell (Recommended)

```powershell
# Start the service
.\service_manager.ps1 -Start

# Check status
.\service_manager.ps1 -Status

# Stop the service
.\service_manager.ps1 -Stop

# View logs
.\service_manager.ps1 -Logs
```

### Option 2: Batch Files

```cmd
# Start the service
start_service.bat

# Stop the service
stop_service.bat
```

### Option 3: Python Daemon Manager

```cmd
# Start the service
python daemon.py start

# Check status
python daemon.py status

# Stop the service
python daemon.py stop

# Restart the service
python daemon.py restart
```

## Linux/Unix

### Option 1: Python Daemon Manager

```bash
# Start the service
python3 daemon.py start

# Check status
python3 daemon.py status

# Stop the service
python3 daemon.py stop
```

### Option 2: Systemd Service (Linux)

1. Edit the service file:

    ```bash
    sudo nano video-encoder.service
    ```

2. Update the paths in the file to match your installation

3. Install and start the service:

    ```bash
    sudo cp video-encoder.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable video-encoder
    sudo systemctl start video-encoder
    ```

4. Check status:
    ```bash
    sudo systemctl status video-encoder
    ```

### Option 3: Screen/tmux

```bash
# Using screen
screen -S video-encoder
python3 service.py
# Press Ctrl+A, then D to detach

# Reattach later
screen -r video-encoder

# Using tmux
tmux new-session -d -s video-encoder 'python3 service.py'
tmux attach-session -t video-encoder
```

## Features

-   **Automatic startup**: Service starts automatically on system boot (systemd)
-   **Graceful shutdown**: Handles shutdown signals properly
-   **Logging**: All output goes to log files in the `logs/` directory
-   **PID tracking**: Keeps track of process ID for management
-   **Status monitoring**: Check if service is running and responding
-   **Error recovery**: Automatic restart on crash (systemd)

## Log Files

All services create log files in the `logs/` directory:

-   `service.log` - Main service output
-   `service_output.log` - Service stdout/stderr (Windows batch)
-   `install.log` - Dependency installation logs
-   `service.pid` - Process ID file

## Dashboard Access

Once running in background, access the dashboard at:

-   **Local**: http://localhost:8000
-   **Network**: http://YOUR_IP:8000 (if firewall allows)

## Troubleshooting

### Service won't start

1. Check Python installation: `python --version`
2. Check FFmpeg installation: `ffmpeg -version`
3. Check .env configuration
4. Check logs for error messages

### Service stops unexpectedly

1. Check logs for error messages
2. Ensure FFmpeg is accessible
3. Check disk space for temporary files
4. Verify Bunny CDN credentials

### Can't access dashboard

1. Check if service is running: `python daemon.py status`
2. Test local access: http://localhost:8000
3. Check firewall settings for port 8000
4. Check network configuration

## Production Recommendations

1. **Use systemd** (Linux) or **Windows Service** for production
2. **Set up log rotation** to prevent log files from growing too large
3. **Monitor disk space** for temporary video files
4. **Use a reverse proxy** (nginx/apache) for HTTPS and domain access
5. **Set up monitoring** and alerting for service health
6. **Regular backups** of configuration and logs

## Security Notes

-   The service runs on all interfaces (0.0.0.0:8000) by default
-   Consider using a reverse proxy with authentication for public access
-   Ensure proper firewall configuration
-   Keep FFmpeg and Python dependencies updated
