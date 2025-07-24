import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import uuid

from .ffmpeg_worker import ffmpeg_worker

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class EncodingJob:
    id: str
    input_file: str
    output_file: str
    codec: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = None
    error_message: Optional[str] = None
    file_size_before: Optional[int] = None
    file_size_after: Optional[int] = None
    remote_path: Optional[str] = None  # Store the original remote path for download
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = {}

class JobQueue:
    def __init__(self, max_concurrent_jobs: int = 1):
        self.jobs: Dict[str, EncodingJob] = {}
        self.pending_jobs: List[str] = []
        self.running_jobs: List[str] = []
        self.max_concurrent_jobs = max_concurrent_jobs
        self.is_processing = False
        self.worker_thread = None
        self._lock = threading.Lock()
        
    def add_job(self, input_file: str, output_file: str, codec: str) -> str:
        """Add a new encoding job to the queue"""
        job_id = str(uuid.uuid4())
        
        # Get input file size
        file_size = None
        try:
            if os.path.exists(input_file):
                file_size = os.path.getsize(input_file)
        except Exception as e:
            logger.warning(f"Could not get file size for {input_file}: {e}")
        
        job = EncodingJob(
            id=job_id,
            input_file=input_file,
            output_file=output_file,
            codec=codec,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            file_size_before=file_size
        )
        
        with self._lock:
            self.jobs[job_id] = job
            self.pending_jobs.append(job_id)
        
        logger.info(f"Added job {job_id} to queue: {input_file} -> {output_file}")
        
        # Start processing if not already running
        if not self.is_processing:
            self.start_processing()
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[EncodingJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[EncodingJob]:
        """Get all jobs ordered by creation time"""
        return sorted(self.jobs.values(), key=lambda x: x.created_at, reverse=True)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        with self._lock:
            pending_count = len(self.pending_jobs)
            running_count = len(self.running_jobs)
            completed_count = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
            failed_count = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
            
        return {
            'pending': pending_count,
            'running': running_count,
            'completed': completed_count,
            'failed': failed_count,
            'total': len(self.jobs),
            'is_processing': self.is_processing
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        with self._lock:
            if job.status == JobStatus.PENDING:
                # Remove from pending queue
                if job_id in self.pending_jobs:
                    self.pending_jobs.remove(job_id)
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                logger.info(f"Cancelled pending job {job_id}")
                return True
            elif job.status == JobStatus.RUNNING:
                # Stop the running encoding
                if job_id in self.running_jobs:
                    success, message = ffmpeg_worker.stop_encoding()
                    if success:
                        job.status = JobStatus.CANCELLED
                        job.completed_at = datetime.now()
                        job.error_message = "Cancelled by user"
                        self.running_jobs.remove(job_id)
                        logger.info(f"Cancelled running job {job_id}")
                        return True
                    else:
                        logger.error(f"Failed to cancel running job {job_id}: {message}")
                        return False
        
        return False
    
    def clear_completed_jobs(self) -> int:
        """Clear all completed and failed jobs"""
        with self._lock:
            completed_job_ids = [
                job_id for job_id, job in self.jobs.items() 
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
            ]
            
            for job_id in completed_job_ids:
                del self.jobs[job_id]
            
            logger.info(f"Cleared {len(completed_job_ids)} completed jobs")
            return len(completed_job_ids)
    
    def start_processing(self):
        """Start the job processing worker thread"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.worker_thread = threading.Thread(target=self._process_jobs, daemon=True)
        self.worker_thread.start()
        logger.info("Started job queue processing")
    
    def stop_processing(self):
        """Stop the job processing"""
        self.is_processing = False
        
        # Cancel any running jobs
        with self._lock:
            for job_id in self.running_jobs.copy():
                self.cancel_job(job_id)
        
        logger.info("Stopped job queue processing")
    
    def _process_jobs(self):
        """Main job processing loop"""
        while self.is_processing:
            try:
                # Check if we can start a new job
                with self._lock:
                    can_start_job = (
                        len(self.running_jobs) < self.max_concurrent_jobs and 
                        len(self.pending_jobs) > 0
                    )
                    
                    if can_start_job:
                        job_id = self.pending_jobs.pop(0)
                        self.running_jobs.append(job_id)
                        job = self.jobs[job_id]
                
                if can_start_job:
                    self._execute_job(job)
                else:
                    # No jobs to process, sleep briefly
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in job processing loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _execute_job(self, job: EncodingJob):
        """Execute a single encoding job with download/encode/upload workflow"""
        logger.info(f"Starting job {job.id}: {job.input_file}")
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            # Import here to avoid circular imports
            from .bunny_client import download_file, upload_file
            
            # Extract filename and create paths
            filename = os.path.basename(job.input_file)
            input_path = job.input_file  # This should be the local path
            output_filename = f"{filename.rsplit('.', 1)[0]}.mp4"
            output_path = job.output_file
            
            # Create directories if they don't exist
            os.makedirs("./input", exist_ok=True)
            os.makedirs("./output", exist_ok=True)
            
            # Step 1: Download (if input_path doesn't exist locally)
            if not os.path.exists(input_path):
                # This means we need to download from Bunny CDN
                # Use the stored remote_path or derive it from the filename
                if job.remote_path:
                    remote_path = job.remote_path
                else:
                    # Fallback: try to derive from input_file path
                    remote_path = job.input_file.replace("./input/", "")
                
                logger.info(f"Downloading {remote_path} to {input_path}")
                download_file(remote_path, input_path)
            
            # Create progress callback
            def progress_callback(progress_data):
                job.progress = progress_data
            
            # Step 2: Run the encoding
            success, message = ffmpeg_worker.run_ffmpeg(
                input_path, 
                output_path, 
                job.codec,
                progress_callback
            )
            
            if not success:
                raise Exception(f"Encoding failed: {message}")
            
            # Calculate compression statistics
            if os.path.exists(input_path) and os.path.exists(output_path):
                original_size = os.path.getsize(input_path)
                compressed_size = os.path.getsize(output_path)
                job.file_size_before = original_size
                job.file_size_after = compressed_size
            
            # Step 3: Upload the encoded file
            upload_path = f"encoded/{output_filename}"
            logger.info(f"Uploading {output_path} to {upload_path}")
            upload_file(output_path, upload_path)
            
            # Step 4: Cleanup local files
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup warning: {cleanup_error}")
            
            # Update job status
            job.completed_at = datetime.now()
            job.status = JobStatus.COMPLETED
            logger.info(f"Job {job.id} completed successfully")
                
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Job {job.id} failed with exception: {e}")
            
            # Cleanup on failure
            try:
                for cleanup_file in [input_path, output_path]:
                    if 'cleanup_file' in locals() and os.path.exists(cleanup_file):
                        os.remove(cleanup_file)
            except:
                pass
        
        finally:
            # Remove from running jobs
            with self._lock:
                if job.id in self.running_jobs:
                    self.running_jobs.remove(job.id)
    
    def get_job_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get job logs for display"""
        jobs = self.get_all_jobs()[:limit]
        
        logs = []
        for job in jobs:
            log_entry = {
                'id': job.id,
                'input_file': os.path.basename(job.input_file),
                'output_file': os.path.basename(job.output_file),
                'codec': job.codec,
                'status': job.status.value,
                'created_at': job.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'progress': job.progress,
                'error_message': job.error_message
            }
            
            if job.started_at:
                log_entry['started_at'] = job.started_at.strftime("%Y-%m-%d %H:%M:%S")
            
            if job.completed_at:
                log_entry['completed_at'] = job.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                
                # Calculate duration
                if job.started_at:
                    duration = (job.completed_at - job.started_at).total_seconds()
                    log_entry['duration'] = f"{duration:.1f}s"
            
            # Calculate compression ratio
            if job.file_size_before and job.file_size_after:
                ratio = (1 - job.file_size_after / job.file_size_before) * 100
                log_entry['compression_ratio'] = f"{ratio:.1f}%"
                log_entry['size_before'] = self._format_file_size(job.file_size_before)
                log_entry['size_after'] = self._format_file_size(job.file_size_after)
            
            logs.append(log_entry)
        
        return logs
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"

# Global queue instance
encoding_queue = JobQueue(max_concurrent_jobs=1)

def add_encoding_job(input_file: str, output_file: str, codec: str) -> str:
    """Add a new encoding job to the global queue"""
    return encoding_queue.add_job(input_file, output_file, codec)

def get_queue_status() -> Dict[str, Any]:
    """Get current queue status"""
    return encoding_queue.get_queue_status()

def get_job_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Get job logs"""
    return encoding_queue.get_job_logs(limit)

def cancel_job(job_id: str) -> bool:
    """Cancel a job"""
    return encoding_queue.cancel_job(job_id)

def clear_completed_jobs() -> int:
    """Clear completed jobs"""
    return encoding_queue.clear_completed_jobs()

def get_job(job_id: str) -> Optional[EncodingJob]:
    """Get job by ID"""
    return encoding_queue.get_job(job_id)
