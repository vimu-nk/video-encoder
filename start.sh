#!/bin/bash

# Simple Video Encoder Startup Script for Ubuntu
# This script starts the FastAPI application directly

set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Video Encoder Platform..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Working directory: $(pwd)"

# Create necessary directories
mkdir -p logs input output

# Check if Python is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Installing required packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check for GPU capabilities
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits | head -1
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] nvidia-smi not available, checking NVENC via ffmpeg..."
fi

if command -v ffmpeg >/dev/null 2>&1; then
    NVENC_COUNT=$(ffmpeg -hide_banner -encoders 2>/dev/null | grep nvenc | wc -l)
    if [ "$NVENC_COUNT" -gt 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] NVENC encoders available: $NVENC_COUNT"
        ffmpeg -hide_banner -encoders 2>/dev/null | grep nvenc | head -3
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] No NVENC encoders detected - will use CPU encoding"
    fi
else
    echo "Warning: FFmpeg not found!"
fi

# Start the server
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Use python -m uvicorn to ensure proper module loading
exec python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log
