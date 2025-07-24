from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List

from .ffmpeg_worker import (
    run_encoding, get_gpu_info, get_nvenc_capabilities, 
    get_supported_codecs, validate_input_file, get_encoding_status, stop_encoding
)
from .bunny_client import list_files, download_file, upload_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs("logs", exist_ok=True)

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create necessary directories
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Optional static files
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Simple job status tracking (single job at a time) with compression stats
current_job = {
    "status": "idle", 
    "log": "", 
    "progress": 0, 
    "filename": "", 
    "error": None,
    "compression_stats": {
        "original_size": 0,
        "compressed_size": 0,
        "compression_ratio": 0,
        "space_saved_mb": 0
    }
}

# CORS if calling from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_job_status(status, log_message="", progress=None, error=None):
    """Update the current job status"""
    current_job["status"] = status
    if log_message:
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_job["log"] += f"[{timestamp}] {log_message}\n"
    if progress is not None:
        current_job["progress"] = progress
    if error:
        current_job["error"] = error

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, path: str = ""):
    try:
        # Get hardware capabilities first (these should always work)
        gpu_info = get_gpu_info()
        nvenc_caps = get_nvenc_capabilities()
        has_nvenc = any(nvenc_caps.values())
        
        # Try to get files from Bunny CDN
        try:
            files_data = await list_files(path)
        except Exception as bunny_error:
            logger.warning(f"Bunny CDN error: {bunny_error}")
            # Return with empty file list but working hardware info
            files_data = {
                "directories": [], 
                "files": [], 
                "current_path": path, 
                "parent_path": ""
            }
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "files_data": files_data,
            "current_path": path,
            "has_nvenc": has_nvenc,
            "nvenc_caps": nvenc_caps,
            "gpu_info": gpu_info
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Fallback with minimal working data
        try:
            gpu_info = get_gpu_info()
            nvenc_caps = get_nvenc_capabilities()
            has_nvenc = any(nvenc_caps.values())
        except Exception as hw_error:
            logger.error(f"Hardware detection error: {hw_error}")
            gpu_info = {"available": False, "gpus": []}
            nvenc_caps = {"av1": False, "hevc": False, "h264": False}
            has_nvenc = False
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "files_data": {"directories": [], "files": [], "current_path": path, "parent_path": ""}, 
            "error": str(e),
            "current_path": path,
            "has_nvenc": has_nvenc,
            "nvenc_caps": nvenc_caps,
            "gpu_info": gpu_info
        })

@app.get("/browse", response_class=HTMLResponse)
async def browse_directory(request: Request, path: str = ""):
    """AJAX endpoint for directory navigation"""
    try:
        files_data = await list_files(path)
        return templates.TemplateResponse("file_list.html", {
            "request": request,
            "files_data": files_data
        })
    except Exception as e:
        return templates.TemplateResponse("file_list.html", {
            "request": request,
            "files_data": {"directories": [], "files": [], "current_path": path, "parent_path": ""},
            "error": str(e)
        })

@app.post("/encode")
async def start_encoding(background_tasks: BackgroundTasks, 
                        file_path: str = Form(...), 
                        codec: str = Form("x265"),
                        quality: str = Form("medium")):
    try:
        # Check if another job is already running
        if current_job["status"] not in ["idle", "completed", "failed"]:
            return JSONResponse({
                "success": False,
                "error": "Another encoding job is already in progress. Please wait for it to complete."
            }, status_code=409)
        
        # Extract filename from path for display
        filename = file_path.split('/')[-1]
        
        # Initialize job status
        current_job["filename"] = filename
        current_job["status"] = "queued"
        current_job["log"] = f"Job queued for {filename} with codec {codec} at {quality} quality\n"
        current_job["progress"] = 0
        current_job["error"] = None
        
        # Start encoding in background
        background_tasks.add_task(process_encoding_job, file_path, codec, quality, filename)
        
        return JSONResponse({
            "success": True,
            "message": f"Encoding job started for {filename}",
            "filename": filename,
            "codec": codec,
            "quality": quality,
            "redirect_url": "/logs"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

def process_encoding_job(file_path: str, codec: str, quality: str, filename: str):
    """Process a single encoding job"""
    try:
        input_path = f"./input/{filename}"
        # Force MKV extension for output
        output_filename = f"{filename.rsplit('.', 1)[0]}_encoded.mkv"
        output_path = f"./output/{output_filename}"
        
        # Create directories if they don't exist
        os.makedirs("./input", exist_ok=True)
        os.makedirs("./output", exist_ok=True)
        
        # Step 1: Download
        update_job_status("downloading", "📥 Starting download from source storage...")
        download_file(file_path, input_path)
        update_job_status("downloading", "✅ Download completed successfully", progress=20)
        
        # Step 2: Encoding
        update_job_status("encoding", f"🚀 Starting hardware encoding with codec: {codec} at {quality} quality")
        
        def progress_callback(progress_data):
            # Map encoding progress to overall progress (20% to 80%)
            if 'percentage' in progress_data:
                overall_progress = 20 + int((progress_data['percentage'] / 100) * 60)
                update_job_status("encoding", f"⚡ Encoding progress: {progress_data['percentage']}%", progress=overall_progress)
        
        # Use the encoding function with specified codec and quality
        success, message = run_encoding(input_path, output_path, codec, quality, progress_callback)
        
        if not success:
            raise Exception(f"Encoding failed: {message}")
        
        # Calculate compression statistics
        if os.path.exists(input_path) and os.path.exists(output_path):
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            space_saved_mb = (original_size - compressed_size) / (1024*1024)
            
            current_job["compression_stats"] = {
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": round(compression_ratio, 1),
                "space_saved_mb": round(space_saved_mb, 1)
            }
            
            update_job_status("encoding", f"✅ Encoding completed! Saved {compression_ratio:.1f}% space ({space_saved_mb:.1f} MB)", progress=80)
        else:
            update_job_status("encoding", "✅ Hardware encoding completed successfully", progress=80)
        
        # Step 3: Upload MKV
        update_job_status("uploading", "📤 Starting upload of encoded MKV file...")
        upload_file(output_path, f"encoded/{output_filename}")
        update_job_status("uploading", "✅ Upload completed successfully", progress=95)
        
        # Step 4: Cleanup (original files are already cleaned by run_ffmpeg)
        update_job_status("cleanup", "🗑️ Cleaning up temporary files...")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
                update_job_status("cleanup", f"🗑️ Removed local output file: {output_filename}")
        except Exception as cleanup_error:
            update_job_status("cleanup", f"⚠️ Cleanup warning: {cleanup_error}")
        
        # Job completed with compression stats
        stats = current_job["compression_stats"]
        if stats["compression_ratio"] > 0:
            completion_msg = f"🎉 Job completed! AV1 NVENC encoding saved {stats['compression_ratio']}% space ({stats['space_saved_mb']} MB)"
        else:
            completion_msg = "🎉 Job completed successfully! MKV file encoded with NVENC AV1."
        
        update_job_status("completed", completion_msg, progress=100)
        
    except Exception as e:
        error_msg = f"❌ Job failed: {str(e)}"
        update_job_status("failed", error_msg, error=str(e))
        print(f"Encoding job error: {e}")
        
        # Cleanup on failure
        try:
            for cleanup_file in [input_path, output_path]:
                if os.path.exists(cleanup_file):
                    os.remove(cleanup_file)
        except:
            pass

# Simple status endpoints
@app.get("/job-status")
async def get_current_job_status():
    """Get current job status"""
    return current_job

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs page showing current job status"""
    return templates.TemplateResponse("simple_logs.html", {"request": request})

@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Legacy status page - redirects to logs"""
    return RedirectResponse(url="/logs", status_code=301)

# API endpoints for AJAX calls
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Video Encoder API is running"}

@app.get("/api/status")
async def api_get_status():
    """API endpoint for getting current job status"""
    return current_job

@app.get("/api/test")
async def api_test():
    """Simple test endpoint to check if API is working"""
    try:
        gpu_info = get_gpu_info()
        nvenc_caps = get_nvenc_capabilities()
        return {
            "status": "ok",
            "gpu_info": gpu_info,
            "nvenc_caps": nvenc_caps,
            "message": "API is working correctly"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Error in API test"
        }

@app.get("/api/hardware")
async def api_get_hardware():
    """API endpoint for getting hardware information"""
    try:
        gpu_info = get_gpu_info()
        nvenc_caps = get_nvenc_capabilities()
        
        return {
            "gpu_available": gpu_info.get("available", False),
            "gpus": gpu_info.get("gpus", []),
            "nvenc_caps": nvenc_caps,
            "has_nvenc": any(nvenc_caps.values())
        }
    except Exception as e:
        logger.error(f"Error getting hardware info: {e}")
        return {
            "gpu_available": False,
            "gpus": [],
            "nvenc_caps": {"av1": False, "hevc": False, "h264": False},
            "has_nvenc": False,
            "error": str(e)
        }

@app.post("/api/stop")
async def api_stop_encoding():
    """API endpoint for stopping current encoding"""
    try:
        success, message = stop_encoding()
        if success:
            current_job["status"] = "idle"
            current_job["progress"] = 0
            update_job_status("idle", "Encoding stopped by user")
        
        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error stopping encoding: {e}")
        return {
            "success": False,
            "error": str(e)
        }
