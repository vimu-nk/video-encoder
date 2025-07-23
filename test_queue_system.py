#!/usr/bin/env python3
"""
Test script for the new queue system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.queue_manager import job_queue, JobStatus, get_queue_stats
import time

def test_queue_system():
    """Test the queue management system"""
    print("Testing Video Encoder Queue System")
    print("=" * 50)
    
    # Add some test jobs
    print("\n1. Adding test jobs to queue...")
    job1 = job_queue.add_job("test_video_1.mp4", "fast")
    job2 = job_queue.add_job("folder/test_video_2.mkv", "medium")
    job3 = job_queue.add_job("another/test_video_3.avi", "ultrafast")
    
    print(f"Added job 1: {job1}")
    print(f"Added job 2: {job2}")
    print(f"Added job 3: {job3}")
    
    # Show queue stats
    print("\n2. Queue Statistics:")
    stats = get_queue_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show all jobs
    print("\n3. All Jobs in Queue:")
    jobs = job_queue.get_all_jobs()
    for job in jobs:
        print(f"  {job.id}: {job.file_path} ({job.status.value}) - {job.preset}")
    
    # Test status updates
    print("\n4. Testing status updates...")
    job_queue.update_job_status(job1, JobStatus.DOWNLOADING, "Started download")
    job_queue.update_job_status(job1, JobStatus.ENCODING, "Started encoding", progress=25)
    job_queue.update_job_status(job1, JobStatus.ENCODING, "Encoding progress", progress=50)
    job_queue.update_job_status(job1, JobStatus.UPLOADING, "Started upload", progress=90)
    job_queue.update_job_status(job1, JobStatus.COMPLETED, "Job completed", progress=100)
    
    # Show updated job
    updated_job = job_queue.get_job(job1)
    if updated_job:
        print(f"Updated job {job1}:")
        print(f"  Status: {updated_job.status.value}")
        print(f"  Progress: {updated_job.progress}%")
        print(f"  Log entries: {len(updated_job.log.split('\\n')) - 1}")
    
    # Test failure case
    job_queue.update_job_status(job2, JobStatus.FAILED, "Test failure", error="Mock encoding error")
    
    # Final stats
    print("\n5. Final Queue Statistics:")
    final_stats = get_queue_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    # Test queue processing logic
    print("\n6. Testing queue processing logic...")
    print(f"Can start new job: {job_queue.can_start_new_job()}")
    
    next_job = job_queue.get_next_job()
    if next_job:
        print(f"Next job to process: {next_job.id} - {next_job.file_path}")
    else:
        print("No jobs ready for processing")
    
    print("\n✅ Queue system test completed!")
    print("\nTo view the queue in web interface:")
    print("1. Start the server: uvicorn app.main:app --reload")
    print("2. Visit: http://localhost:8000/logs")

if __name__ == "__main__":
    test_queue_system()
