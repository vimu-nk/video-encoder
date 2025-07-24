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
    get_gpu_info, get_nvenc_capabilities, 
    get_supported_codecs, validate_input_file
)
from .bunny_client import list_files, download_file, upload_file
from .queue_manager import (
    add_encoding_job, get_queue_status, get_job_logs, 
    cancel_job, clear_completed_jobs, get_job
)

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

# CORS if calling from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def start_encoding(request: Request):
    try:
        # Get form data
        form_data = await request.form()
        file_paths = form_data.getlist("file_path")  # Get list of selected files
        codec = form_data.get("codec", "hevc_nvenc")
        
        if not file_paths:
            return JSONResponse({
                "success": False,
                "error": "No files selected"
            }, status_code=400)
        
        job_ids = []
        filenames = []
        
        # Process each selected file
        for file_path in file_paths:
            # Extract filename from path for display
            filename = file_path.split('/')[-1]
            
            # Create input/output paths
            input_path = f"./input/{filename}"
            output_filename = f"{filename.rsplit('.', 1)[0]}.mp4"
            output_path = f"./output/{output_filename}"
            
            # Add job to queue with remote file path for download
            job_id = add_encoding_job(input_path, output_path, codec)
            
            # Store the original remote path for download
            job = get_job(job_id)
            if job:
                job.remote_path = file_path  # Store the original remote path
            
            job_ids.append(job_id)
            filenames.append(filename)
        
        return JSONResponse({
            "success": True,
            "message": f"Added {len(job_ids)} job(s) to queue",
            "job_ids": job_ids,
            "filename": filenames[0] if len(filenames) == 1 else f"{len(filenames)} files",
            "codec": codec,
            "redirect_url": "/logs"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# API endpoints for queue management
@app.get("/api/queue/status")
async def api_get_queue_status():
    """Get current queue status"""
    return get_queue_status()

@app.get("/api/queue/logs")
async def api_get_job_logs(limit: int = 100):
    """Get job logs"""
    return get_job_logs(limit)

@app.post("/api/queue/cancel/{job_id}")
async def api_cancel_job(job_id: str):
    """Cancel a specific job"""
    try:
        success = cancel_job(job_id)
        return {
            "success": success,
            "message": "Job cancelled successfully" if success else "Failed to cancel job"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/queue/clear")
async def api_clear_completed_jobs():
    """Clear all completed jobs"""
    try:
        count = clear_completed_jobs()
        return {
            "success": True,
            "message": f"Cleared {count} completed jobs"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/job-status")
async def get_current_job_status():
    """Legacy endpoint - returns queue status for compatibility"""
    return get_queue_status()

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs page showing queue status and job logs"""
    return templates.TemplateResponse("logs.html", {"request": request})

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
    """API endpoint for getting queue status (legacy compatibility)"""
    return get_queue_status()

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
            "nvenc_caps": {"hevc": False, "h264": False},
            "has_nvenc": False,
            "error": str(e)
        }

@app.post("/api/stop")
async def api_stop_encoding():
    """API endpoint for stopping/cancelling jobs"""
    try:
        # Get currently running jobs and cancel them
        queue_status = get_queue_status()
        if queue_status['running'] > 0:
            # For now, we'll need to get the running job ID
            # This is a simplified approach - in practice you might want to cancel all running jobs
            return {
                "success": True,
                "message": "Use /api/queue/cancel/{job_id} to cancel specific jobs"
            }
        else:
            return {
                "success": True,
                "message": "No running jobs to cancel"
            }
    except Exception as e:
        logger.error(f"Error in stop endpoint: {e}")
        return {
            "success": False,
            "error": str(e)
        }
