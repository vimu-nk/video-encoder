# Video Encoder Platform

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

1. User selects a video file from the dashboard
2. System downloads the file from source storage
3. FFmpeg encodes the video with H.265
4. Encoded video is uploaded to destination storage
5. Local temporary files are cleaned up
6. Job status is updated throughout the process

## Troubleshooting

-   **FFmpeg not found:** Ensure FFmpeg is installed and in your system PATH
-   **Bunny CDN errors:** Check your API keys and storage zone configurations
-   **Encoding fails:** Check the job logs in the status page for detailed error messages

## Development

To run in development mode with auto-reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
