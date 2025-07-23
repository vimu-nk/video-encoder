from fastapi import FastAPI, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .bunny_client import list_files, download_file, upload_file
from .ffmpeg_worker import encode_to_hevc

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

BASE_DIR = Path("/tmp/videos")
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

job_status = {}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    files = await list_files()
    return templates.TemplateResponse("dashboard.html", {"request": request, "files": files})

@app.post("/encode")
async def start_encoding(request: Request, background_tasks: BackgroundTasks, filename: str = Form(...)):
    input_path = INPUT_DIR / filename
    output_path = OUTPUT_DIR / f"{filename.rsplit('.',1)[0]}.mkv"

    # Download file from source zone
    download_file(filename, input_path)

    def task():
        job_status[filename] = {"status": "encoding", "log": ""}
        result = encode_to_hevc(str(input_path), str(output_path))
        if result.returncode == 0:
            upload_file(output_path, output_path.name)
            job_status[filename] = {"status": "done", "log": result.stdout.decode()}
        else:
            job_status[filename] = {"status": "error", "log": result.stderr.decode()}

    background_tasks.add_task(task)
    return {"message": "Encoding started", "file": filename}

@app.get("/status", response_class=HTMLResponse)
async def get_status(request: Request):
    return templates.TemplateResponse("status.html", {"request": request, "status": job_status})
