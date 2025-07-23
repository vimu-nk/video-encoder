#!/usr/bin/env python3
"""
Background service runner for the Video Encoder Platform
This script runs the application as a daemon/background service
"""
import uvicorn
import os
import sys
import signal
import logging
from pathlib import Path

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'encoder_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def run_service():
    """Run the service"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.warning(".env file not found. Please create one with your Bunny CDN credentials.")
        logger.warning("See .env.example for the required format.")
    
    # Check if ffmpeg is available
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("✓ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("⚠ Warning: FFmpeg not found. Please install FFmpeg and add it to your PATH.")
        logger.warning("Download from: https://ffmpeg.org/download.html")
    
    logger.info("Starting Video Encoder Platform as background service...")
    logger.info("Dashboard will be available at: http://localhost:8000")
    logger.info("Logs are being written to: logs/encoder_service.log")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False  # Disable reload for production
        )
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_service()
