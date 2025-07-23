# Vi## Features

-   **Directory Navigation:** Browse through Bunny CDN sto## API Endpoints

-   `GET /` - Dashboard interface with directory navigation
-   `GET /browse?path=<path>` - AJAX endpoint for directory browsing
-   `POST /encode` - Start encoding job (accepts `file_path` parameter)
-   `GET /status` - Interactive status page with real-time updates
-   `GET /api/status` - JSON status API for AJAX updates

## New Features

### Directory Navigation

-   Browse through nested folders in your Bunny CDN storage
-   Breadcrumb navigation showing current path
-   One-click navigation to parent directories
-   Automatic filtering for video files only

### Real-time Status Updates

-   Status page updates automatically every 3 seconds
-   Toggle auto-refresh on/off
-   Manual refresh button
-   Last updated timestamp
-   No page reload required

### Enhanced User Interface

-   Clean, modern design with icons
-   Visual indicators for different job states
-   Progress bars with smooth animations
-   File size display and modification dates
-   Responsive layoutolders and subfolders
-   **File Filtering:** Automatically shows only video files (mp4, avi, mkv, mov, wmv, flv, webm, m4v)
-   **Real-time Status Updates:** Job status updates without page refresh (auto-refresh every 3 seconds)
-   **Background Encoding:** Non-blocking video encoding with progress tracking
-   **AJAX Navigation:** Smooth directory browsing without page reloads
-   **Automatic Upload:** Encoded videos uploaded to destination storage
-   **Local Cleanup:** Temporary files removed after processing
-   **Responsive Interface:** Clean, modern web interfaceoder Platform

A web-based video encoding platform that downloads videos from Bunny CDN source storage, encodes them using FFmpeg with H.265, and uploads the results to destination storage.

## Features

-   Web dashboard to select videos from source storage
-   Background video encoding with progress tracking
-   Real-time status monitoring
-   Automatic upload to destination storage
-   Local file cleanup after processing

## Prerequisites

1. **Python 3.7+**
2. **FFmpeg** - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
3. **Bunny CDN Storage Zones** - Both source and destination

## Setup

1. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2. **Configure environment:**

    ```bash
    cp .env.example .env
    # Edit .env with your Bunny CDN credentials
    ```

3. **Run the application:**

    **For development/testing:**

    ```bash
    python run.py
    ```

    **For background service (keeps running after terminal closes):**

    Windows (PowerShell):

    ```powershell
    .\service_manager.ps1 -Start
    ```

    Windows (Simple menu):

    ```cmd
    manage_service.bat
    ```

    Cross-platform:

    ```bash
    python daemon.py start
    ```

4. **Access the dashboard:**
   Open [http://localhost:8000](http://localhost:8000) in your browser

## Running as Background Service

The platform can run as a background service that continues running even after you close the terminal.

### Windows Options:

1. **PowerShell Service Manager** (Recommended):

    ```powershell
    .\service_manager.ps1 -Start    # Start service
    .\service_manager.ps1 -Status   # Check status
    .\service_manager.ps1 -Stop     # Stop service
    ```

2. **Interactive Menu**:

    ```cmd
    manage_service.bat
    ```

3. **Cross-platform Daemon**:
    ```cmd
    python daemon.py start
    ```

### Linux/Unix Options:

1. **Python Daemon**:

    ```bash
    python3 daemon.py start
    python3 daemon.py status
    python3 daemon.py stop
    ```

2. **Systemd Service** (see `BACKGROUND_SERVICE.md` for details)

For complete background service documentation, see: **[BACKGROUND_SERVICE.md](BACKGROUND_SERVICE.md)**

## DigitalOcean Ubuntu Deployment

For production deployment on DigitalOcean Ubuntu droplets:

### Quick Deploy

```bash
# Download and run the deployment script
wget https://raw.githubusercontent.com/your-username/video-encoder/main/deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh
```

### Manual Steps

1. **Prepare server:**

    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install python3 python3-pip python3-venv git nginx ffmpeg -y
    ```

2. **Deploy application:**

    ```bash
    sudo adduser --system --group --home /opt/video-encoder video-encoder
    sudo -u video-encoder git clone https://github.com/your-username/video-encoder.git /opt/video-encoder/app
    cd /opt/video-encoder/app
    sudo -u video-encoder python3 -m venv /opt/video-encoder/venv
    sudo -u video-encoder /opt/video-encoder/venv/bin/pip install -r requirements.txt
    ```

3. **Configure service:**

    ```bash
    sudo cp video-encoder.service /etc/systemd/system/
    sudo systemctl enable video-encoder
    sudo systemctl start video-encoder
    ```

4. **Set up reverse proxy:**
    ```bash
    sudo cp nginx-video-encoder /etc/nginx/sites-available/video-encoder
    sudo ln -s /etc/nginx/sites-available/video-encoder /etc/nginx/sites-enabled/
    sudo systemctl reload nginx
    ```

### Management Commands

```bash
# Service management
sudo systemctl start|stop|restart video-encoder
sudo journalctl -u video-encoder -f

# Application management (after deployment)
video-encoder-manage start|stop|restart|status|logs|update
video-encoder-manage ssl your-domain.com

# Health monitoring
/opt/video-encoder/app/health_check.sh
```

For detailed Ubuntu deployment guide, see: **[UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md)**

Edit `.env` file with your Bunny CDN credentials:

```env
SOURCE_BUNNY_API_KEY=your_source_api_key
SOURCE_BUNNY_STORAGE_ZONE=your_source_zone
SOURCE_BUNNY_STORAGE_HOST=sg.storage.bunnycdn.com

DEST_BUNNY_API_KEY=your_dest_api_key
DEST_BUNNY_STORAGE_ZONE=your_dest_zone
DEST_BUNNY_STORAGE_HOST=storage.bunnycdn.com
```

## Encoding Settings

The platform uses the following FFmpeg settings for optimal quality/size balance:

-   **Video Codec:** H.265 (libx265)
-   **Preset:** slow (better compression)
-   **CRF:** 28 (good quality/size balance)
-   **Pixel Format:** yuv420p10le (10-bit color)
-   **Audio:** Copy original (no re-encoding)

## API Endpoints

-   `GET /` - Dashboard interface
-   `POST /encode` - Start encoding job
-   `GET /status` - Status page with all jobs
-   `GET /api/status` - JSON status API

## Workflow

1. **Browse Files:** Navigate through directories in your Bunny CDN source storage
2. **Select Video:** Choose a video file from any folder or subfolder
3. **Start Encoding:** Click "Start Encoding" to begin the process
4. **Monitor Progress:** Watch real-time progress on the status page
5. **Auto-Processing:** System automatically downloads → encodes → uploads → cleans up
6. **Completion:** Encoded video appears in destination storage

## Testing Navigation

Run the test script to verify your Bunny CDN configuration:

```bash
python test_navigation.py
```

## Troubleshooting

-   **FFmpeg not found:** Ensure FFmpeg is installed and in your system PATH
-   **Bunny CDN errors:** Check your API keys and storage zone configurations
-   **Encoding fails:** Check the job logs in the status page for detailed error messages

## Development

To run in development mode with auto-reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
