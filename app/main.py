from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Global progress store - should use a proper database in production
job_status = {}

# CORS if calling from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_progress(filename, percent):
    if filename not in job_status:
        job_status[filename] = {"status": "encoding", "log": "", "percent": 0}
    job_status[filename]["percent"] = percent
    job_status[filename]["status"] = "encoding"
    job_status[filename]["log"] += f"Progress: {percent}%\n"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        files = await list_files()
        return templates.TemplateResponse("dashboard.html", {"request": request, "files": files})
    except Exception as e:
        return templates.TemplateResponse("dashboard.html", {"request": request, "files": [], "error": str(e)})

@app.post("/encode")
async def start_encoding(background_tasks: BackgroundTasks, filename: str = Form(...)):
    try:
        # Initialize job status
        job_status[filename] = {"status": "downloading", "log": "Starting download...\n", "percent": 0}
        
        input_path = f"./input/{filename}"
        output_filename = f"{filename.rsplit('.', 1)[0]}_encoded.mkv"
        output_path = f"./output/{output_filename}"

        def encode_job():
            try:
                # Download file from source storage
                job_status[filename]["log"] += "Downloading from source storage...\n"
                download_file(filename, input_path)
                job_status[filename]["log"] += "Download completed.\n"
                
                # Start encoding
                job_status[filename]["status"] = "encoding"
                job_status[filename]["log"] += "Starting encoding...\n"
                
                def progress_callback(percent):
                    update_progress(filename, percent)
                
                return_code = run_ffmpeg(input_path, output_path, progress_callback=progress_callback)
                
                if return_code == 0:
                    job_status[filename]["log"] += "Encoding completed successfully.\n"
                    job_status[filename]["status"] = "uploading"
                    job_status[filename]["log"] += "Uploading to destination storage...\n"
                    
                    # Upload to destination storage
                    upload_file(output_path, output_filename)
                    job_status[filename]["log"] += "Upload completed.\n"
                    job_status[filename]["status"] = "completed"
                    job_status[filename]["percent"] = 100
                    
                    # Clean up local files
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    job_status[filename]["log"] += "Local files cleaned up.\n"
                else:
                    job_status[filename]["status"] = "failed"
                    job_status[filename]["log"] += f"Encoding failed with return code: {return_code}\n"
                    
            except Exception as e:
                job_status[filename]["status"] = "failed"
                job_status[filename]["log"] += f"Error: {str(e)}\n"

        background_tasks.add_task(encode_job)
        return RedirectResponse(url="/status", status_code=303)
        
    except Exception as e:
        return {"error": f"Failed to start encoding: {str(e)}"}

@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request, "status": job_status})

@app.get("/api/status")
def get_status():
    return job_status
