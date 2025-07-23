from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os
import asyncio

from .ffmpeg_worker import run_ffmpeg
from .bunny_client import list_files, download_file, upload_file

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create necessary directories
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Optional static files
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Simple job status tracking (single job at a time)
current_job = {"status": "idle", "log": "", "progress": 0, "filename": "", "error": None}

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
        files_data = await list_files(path)
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "files_data": files_data,
            "current_path": path
        })
    except Exception as e:
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "files_data": {"directories": [], "files": [], "current_path": path, "parent_path": ""}, 
            "error": str(e),
            "current_path": path
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
async def start_encoding(background_tasks: BackgroundTasks, file_path: str = Form(...), preset: str = Form("fast")):
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
        current_job["log"] = f"Job queued for {filename} with preset {preset}\n"
        current_job["progress"] = 0
        current_job["error"] = None
        
        # Start encoding in background
        background_tasks.add_task(process_encoding_job, file_path, preset, filename)
        
        return JSONResponse({
            "success": True,
            "message": f"Encoding job started for {filename}",
            "filename": filename,
            "preset": preset,
            "redirect_url": "/logs"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

def process_encoding_job(file_path: str, preset: str, filename: str):
    """Process a single encoding job"""
    try:
        input_path = f"./input/{filename}"
        output_filename = f"{filename.rsplit('.', 1)[0]}_encoded.mkv"
        output_path = f"./output/{output_filename}"
        
        # Create directories if they don't exist
        os.makedirs("./input", exist_ok=True)
        os.makedirs("./output", exist_ok=True)
        
        # Step 1: Download
        update_job_status("downloading", "Starting download from source storage...")
        download_file(file_path, input_path)
        update_job_status("downloading", "Download completed successfully", progress=30)
        
        # Step 2: Encode
        update_job_status("encoding", f"Starting encoding with preset: {preset}")
        
        def progress_callback(percent):
            # Map encoding progress to overall progress (30% to 90%)
            overall_progress = 30 + int((percent / 100) * 60)
            update_job_status("encoding", f"Encoding progress: {percent}%", progress=overall_progress)
        
        return_code = run_ffmpeg(input_path, output_path, progress_callback=progress_callback, preset_name=preset)
        
        if return_code != 0:
            raise Exception(f"FFmpeg encoding failed with return code: {return_code}")
        
        update_job_status("encoding", "Encoding completed successfully", progress=90)
        
        # Step 3: Upload
        update_job_status("uploading", "Starting upload to destination storage...")
        upload_file(output_path, output_filename)
        update_job_status("uploading", "Upload completed successfully", progress=95)
        
        # Step 4: Cleanup
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        
        update_job_status("completed", "Job completed successfully. Local files cleaned up.", progress=100)
        
    except Exception as e:
        error_msg = f"Job failed: {str(e)}"
        update_job_status("failed", error_msg, error=str(e))
        
        # Cleanup on failure
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass  # Ignore cleanup errors

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
@app.get("/api/status")
async def api_get_status():
    """API endpoint for getting current job status"""
    return current_job
