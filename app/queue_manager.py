import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Optional
import threading
import time

class JobStatus(Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    ENCODING = "encoding"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class EncodingJob:
    id: str
    file_path: str
    preset: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    log: str = ""
    error: Optional[str] = None
    input_file: Optional[str] = None
    output_file: Optional[str] = None

class JobQueue:
    def __init__(self, max_concurrent_jobs=1):
        self.jobs: List[EncodingJob] = []
        self.max_concurrent_jobs = max_concurrent_jobs
        self.running_jobs = 0
        self.lock = threading.Lock()
        self.queue_file = "job_queue.json"
        self.load_queue()
        
    def add_job(self, file_path: str, preset: str = "fast") -> str:
        """Add a new job to the queue"""
        job_id = f"job_{int(time.time())}_{len(self.jobs)}"
        
        job = EncodingJob(
            id=job_id,
            file_path=file_path,
            preset=preset,
            status=JobStatus.QUEUED,
            created_at=datetime.now().isoformat(),
            log=f"Job created for {file_path} with preset {preset}\n"
        )
        
        with self.lock:
            self.jobs.append(job)
            self.save_queue()
            
        return job_id
    
    def get_job(self, job_id: str) -> Optional[EncodingJob]:
        """Get a specific job by ID"""
        with self.lock:
            return next((job for job in self.jobs if job.id == job_id), None)
    
    def get_all_jobs(self) -> List[EncodingJob]:
        """Get all jobs"""
        with self.lock:
            return self.jobs.copy()
    
    def get_queued_jobs(self) -> List[EncodingJob]:
        """Get jobs that are waiting to be processed"""
        with self.lock:
            return [job for job in self.jobs if job.status == JobStatus.QUEUED]
    
    def get_running_jobs(self) -> List[EncodingJob]:
        """Get jobs that are currently being processed"""
        with self.lock:
            return [job for job in self.jobs if job.status in [JobStatus.DOWNLOADING, JobStatus.ENCODING, JobStatus.UPLOADING]]
    
    def update_job_status(self, job_id: str, status: JobStatus, log_message: str = "", progress: Optional[int] = None, error: Optional[str] = None):
        """Update job status and add log message"""
        with self.lock:
            job = next((job for job in self.jobs if job.id == job_id), None)
            if job:
                job.status = status
                if log_message:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    job.log += f"[{timestamp}] {log_message}\n"
                if progress is not None:
                    job.progress = progress
                if error:
                    job.error = error
                    
                # Update timestamps
                if status in [JobStatus.DOWNLOADING] and not job.started_at:
                    job.started_at = datetime.now().isoformat()
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    job.completed_at = datetime.now().isoformat()
                    
                self.save_queue()
                return True
        return False
    
    def can_start_new_job(self) -> bool:
        """Check if we can start a new job based on concurrent limit"""
        with self.lock:
            running_count = len(self.get_running_jobs())
            return running_count < self.max_concurrent_jobs
    
    def get_next_job(self) -> Optional[EncodingJob]:
        """Get the next job to process"""
        if self.can_start_new_job():
            queued_jobs = self.get_queued_jobs()
            return queued_jobs[0] if queued_jobs else None
        return None
    
    def remove_completed_jobs(self, keep_last_n: int = 50):
        """Remove old completed/failed jobs, keeping the last N"""
        with self.lock:
            completed_jobs = [job for job in self.jobs if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]]
            if len(completed_jobs) > keep_last_n:
                # Sort by completion time and keep the most recent
                completed_jobs.sort(key=lambda x: x.completed_at or "")
                jobs_to_remove = completed_jobs[:-keep_last_n]
                
                for job in jobs_to_remove:
                    self.jobs.remove(job)
                
                self.save_queue()
                return len(jobs_to_remove)
        return 0
    
    def save_queue(self):
        """Save queue to disk"""
        try:
            with open(self.queue_file, 'w') as f:
                queue_data = [asdict(job) for job in self.jobs]
                # Convert enum to string
                for job_data in queue_data:
                    job_data['status'] = job_data['status'].value
                json.dump(queue_data, f, indent=2)
        except Exception as e:
            print(f"Error saving queue: {e}")
    
    def load_queue(self):
        """Load queue from disk"""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r') as f:
                    queue_data = json.load(f)
                    self.jobs = []
                    for job_data in queue_data:
                        # Convert string back to enum
                        job_data['status'] = JobStatus(job_data['status'])
                        job = EncodingJob(**job_data)
                        self.jobs.append(job)
        except Exception as e:
            print(f"Error loading queue: {e}")
            self.jobs = []

# Global queue instance
job_queue = JobQueue(max_concurrent_jobs=1)  # Process one job at a time

def get_queue_stats():
    """Get queue statistics"""
    all_jobs = job_queue.get_all_jobs()
    return {
        "total_jobs": len(all_jobs),
        "queued": len([j for j in all_jobs if j.status == JobStatus.QUEUED]),
        "running": len([j for j in all_jobs if j.status in [JobStatus.DOWNLOADING, JobStatus.ENCODING, JobStatus.UPLOADING]]),
        "completed": len([j for j in all_jobs if j.status == JobStatus.COMPLETED]),
        "failed": len([j for j in all_jobs if j.status == JobStatus.FAILED])
    }
