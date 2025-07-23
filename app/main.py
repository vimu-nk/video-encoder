from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .ffmpeg_worker import run_ffmpeg

app = FastAPI()

# Optional static files
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Global progress store (simplified for 1 task)
progress = {"status": "idle", "percent": 0, "file": ""}

# CORS if calling from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_progress(p):
    progress["percent"] = p
    progress["status"] = "encoding"

@app.post("/encode")
def start_encoding(filename: str, background_tasks: BackgroundTasks):
    input_path = f"./input/{filename}"
    output_path = f"./output/{filename.rsplit('.', 1)[0]}.mkv"

    if not os.path.exists(input_path):
        return {"error": "File not found."}

    def encode_job():
        progress["file"] = filename
        progress["percent"] = 0
        progress["status"] = "encoding"
        run_ffmpeg(input_path, output_path, progress_callback=update_progress)
        progress["status"] = "done"

    background_tasks.add_task(encode_job)
    return {"message": "Encoding started."}

@app.get("/status")
def get_status():
    return progress
