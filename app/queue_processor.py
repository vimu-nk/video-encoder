import asyncio
import threading
import time
import os
from app.queue_manager import job_queue, JobStatus
from app.bunny_client import download_file, upload_file
from app.ffmpeg_worker import run_ffmpeg

class QueueProcessor:
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the background queue processor"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_loop, daemon=True)
            self.thread.start()
            print("Queue processor started")
    
    def stop(self):
        """Stop the background queue processor"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Queue processor stopped")
    
    def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                job = job_queue.get_next_job()
                if job:
                    self._process_job(job)
                else:
                    time.sleep(5)  # Wait 5 seconds before checking again
            except Exception as e:
                print(f"Error in queue processor: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _process_job(self, job):
        """Process a single encoding job"""
        try:
            # Extract filename from path for display
            filename = job.file_path.split('/')[-1]
            input_path = f"./input/{filename}"
            output_filename = f"{filename.rsplit('.', 1)[0]}_encoded.mkv"
            output_path = f"./output/{output_filename}"
            
            # Create directories if they don't exist
            os.makedirs("./input", exist_ok=True)
            os.makedirs("./output", exist_ok=True)
            
            # Update job with file paths
            job.input_file = input_path
            job.output_file = output_path
            
            # Step 1: Download
            job_queue.update_job_status(
                job.id, 
                JobStatus.DOWNLOADING, 
                "Starting download from source storage..."
            )
            
            download_file(job.file_path, input_path)
            job_queue.update_job_status(
                job.id, 
                JobStatus.DOWNLOADING, 
                "Download completed successfully", 
                progress=33
            )
            
            # Step 2: Encode
            job_queue.update_job_status(
                job.id, 
                JobStatus.ENCODING, 
                f"Starting encoding with preset: {job.preset}"
            )
            
            def progress_callback(percent):
                # Map encoding progress to overall progress (33% to 90%)
                overall_progress = 33 + int((percent / 100) * 57)
                job_queue.update_job_status(
                    job.id, 
                    JobStatus.ENCODING, 
                    f"Encoding progress: {percent}%", 
                    progress=overall_progress
                )
            
            return_code = run_ffmpeg(
                input_path, 
                output_path, 
                progress_callback=progress_callback, 
                preset_name=job.preset
            )
            
            if return_code != 0:
                raise Exception(f"FFmpeg encoding failed with return code: {return_code}")
            
            job_queue.update_job_status(
                job.id, 
                JobStatus.ENCODING, 
                "Encoding completed successfully", 
                progress=90
            )
            
            # Step 3: Upload
            job_queue.update_job_status(
                job.id, 
                JobStatus.UPLOADING, 
                "Starting upload to destination storage..."
            )
            
            upload_file(output_path, output_filename)
            
            job_queue.update_job_status(
                job.id, 
                JobStatus.UPLOADING, 
                "Upload completed successfully", 
                progress=95
            )
            
            # Step 4: Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            
            job_queue.update_job_status(
                job.id, 
                JobStatus.COMPLETED, 
                "Job completed successfully. Local files cleaned up.", 
                progress=100
            )
            
        except Exception as e:
            error_msg = f"Job failed: {str(e)}"
            job_queue.update_job_status(
                job.id, 
                JobStatus.FAILED, 
                error_msg, 
                error=str(e)
            )
            
            # Cleanup on failure
            try:
                if job.input_file and os.path.exists(job.input_file):
                    os.remove(job.input_file)
                if job.output_file and os.path.exists(job.output_file):
                    os.remove(job.output_file)
            except:
                pass  # Ignore cleanup errors

# Global processor instance
queue_processor = QueueProcessor()
