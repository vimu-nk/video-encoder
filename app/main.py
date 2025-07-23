from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os
import asyncio
from contextlib import asynccontextmanager

from .ffmpeg_worker import run_ffmpeg
from .bunny_client import list_files, download_file, upload_file
from .queue_manager import job_queue, get_queue_stats, JobStatus
from .queue_processor import queue_processor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    queue_processor.start()
    yield
    # Shutdown
    queue_processor.stop()

app = FastAPI(lifespan=lifespan)

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
async def start_encoding(file_path: str = Form(...), preset: str = Form("fast")):
    try:
        # Add job to queue instead of processing immediately
        job_id = job_queue.add_job(file_path, preset)
        
        return JSONResponse({
            "success": True,
            "message": f"Job added to queue successfully",
            "job_id": job_id,
            "file_path": file_path,
            "preset": preset
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Queue management endpoints
@app.get("/queue")
async def get_queue_status():
    """Get current queue status"""
    stats = get_queue_stats()
    jobs = job_queue.get_all_jobs()
    
    # Convert jobs to dict format for JSON response
    jobs_data = []
    for job in jobs:
        job_data = {
            "id": job.id,
            "file_path": job.file_path,
            "preset": job.preset,
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "progress": job.progress,
            "log": job.log,
            "error": job.error
        }
        jobs_data.append(job_data)
    
    return {
        "stats": stats,
        "jobs": jobs_data
    }

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job"""
    job = job_queue.get_job(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    
    return {
        "id": job.id,
        "file_path": job.file_path,
        "preset": job.preset,
        "status": job.status.value,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "progress": job.progress,
        "log": job.log,
        "error": job.error
    }

@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Legacy status page - now redirects to logs"""
    return RedirectResponse(url="/logs", status_code=301)

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """New logs page showing queue status and job history"""
    return templates.TemplateResponse("logs.html", {"request": request})

# API endpoints for AJAX calls
@app.get("/api/queue")
async def api_get_queue():
    """API endpoint for getting queue data"""
    return await get_queue_status()

@app.get("/api/job/{job_id}")
async def api_get_job(job_id: str):
    """API endpoint for getting specific job data"""
    return await get_job_status(job_id)
