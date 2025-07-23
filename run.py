#!/usr/bin/env python3
"""
Startup script for the Video Encoder Platform
"""
import uvicorn
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Please create one with your Bunny CDN credentials.")
        print("See .env.example for the required format.")
    
    # Check if ffmpeg is available
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✓ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Warning: FFmpeg not found. Please install FFmpeg and add it to your PATH.")
        print("Download from: https://ffmpeg.org/download.html")
    
    print("Starting Video Encoder Platform...")
    print("Dashboard will be available at: http://localhost:8000")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
