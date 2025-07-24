#!/usr/bin/env python3
"""
Video Encoder Platform - Direct Python Startup
This script starts the FastAPI application directly using uvicorn
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI application"""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    logger.info("Starting Video Encoder Platform...")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check for GPU capabilities
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_name = result.stdout.strip()
            logger.info(f"NVIDIA GPU detected: {gpu_name}")
        else:
            logger.warning("nvidia-smi not available")
    except Exception as e:
        logger.warning(f"Could not check GPU: {e}")
    
    # Check NVENC capabilities
    try:
        result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            nvenc_count = result.stdout.lower().count('nvenc')
            logger.info(f"NVENC encoders available: {nvenc_count}")
            
            # Show available NVENC encoders
            for line in result.stdout.split('\n'):
                if 'nvenc' in line.lower():
                    logger.info(f"  {line.strip()}")
        else:
            logger.warning("Could not check NVENC capabilities")
    except Exception as e:
        logger.warning(f"Could not check NVENC: {e}")
    
    # Start uvicorn server
    try:
        import uvicorn
        logger.info("Starting uvicorn server...")
        
        # Add current directory to Python path so 'app' module can be found
        sys.path.insert(0, str(script_dir))
        
        # Verify the app module can be imported
        try:
            from app.main import app
            logger.info("Successfully imported app module")
        except ImportError as e:
            logger.error(f"Could not import app module: {e}")
            logger.info("Trying alternative import method...")
            
            # Alternative: run uvicorn as subprocess
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--log-level", "info",
                "--access-log"
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, cwd=script_dir)
            return
        
        # Configure uvicorn
        config = uvicorn.Config(
            app,  # Use the imported app directly
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False,
            workers=1
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    except ImportError:
        logger.error("uvicorn not installed. Please install with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
