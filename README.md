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

    ```bash
    python run.py
    ```

4. **Access the dashboard:**
   Open [http://localhost:8000](http://localhost:8000) in your browser

## Configuration

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
