#!/usr/bin/env python3
"""
Final system test - Web interface with fixed FFmpeg
"""

import sys
import os
import time
import subprocess
import requests
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_video():
    """Create a test video for uploading"""
    test_video = "test_upload_video.mp4"
    
    create_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=15:size=1920x1080:rate=30",
        "-c:v", "libx264",
        "-preset", "medium",
        "-t", "15",
        test_video
    ]
    
    print("Creating test video for upload...")
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        size = os.path.getsize(test_video)
        print(f"✅ Created test video: {test_video} ({size:,} bytes)")
        return test_video
    else:
        print(f"❌ Failed to create test video: {result.stderr}")
        return None

def start_server():
    """Start the FastAPI server"""
    print("Starting FastAPI server...")
    server_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server started successfully")
            return server_process
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to server: {e}")
        return None

def test_web_interface():
    """Test the complete web interface"""
    print("\nFinal System Test")
    print("=" * 30)
    
    # Create test video
    test_video = create_test_video()
    if not test_video:
        return
    
    # Start server
    server_process = start_server()
    if not server_process:
        return
    
    try:
        # Test dashboard access
        print("\n1. Testing dashboard access...")
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Dashboard accessible")
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
        
        # Test logs page
        print("\n2. Testing logs page...")
        response = requests.get("http://localhost:8000/logs")
        if response.status_code == 200:
            print("✅ Logs page accessible")
        else:
            print(f"❌ Logs page failed: {response.status_code}")
        
        # Test file upload and encoding
        print("\n3. Testing file upload and encoding...")
        with open(test_video, 'rb') as f:
            files = {'file': (test_video, f, 'video/mp4')}
            data = {
                'quality': 'fast',
                'upload_to_bunny': 'false'  # Don't upload to avoid API errors
            }
            
            response = requests.post(
                "http://localhost:8000/upload",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                print("✅ File upload successful")
                
                # Monitor job progress
                print("\n4. Monitoring job progress...")
                for i in range(30):  # Monitor for up to 30 seconds
                    status_response = requests.get("http://localhost:8000/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        current_job = status_data.get('current_job')
                        if current_job:
                            print(f"Job status: {current_job.get('status', 'unknown')} - Progress: {current_job.get('progress', 0)}%")
                            if current_job.get('status') == 'completed':
                                print("✅ Encoding completed successfully!")
                                break
                            elif current_job.get('status') == 'failed':
                                print(f"❌ Encoding failed: {current_job.get('error', 'Unknown error')}")
                                break
                        else:
                            print("No active job found")
                            break
                    time.sleep(1)
                else:
                    print("⚠️ Job monitoring timed out")
            else:
                print(f"❌ File upload failed: {response.status_code}")
                if response.text:
                    print(f"Error: {response.text}")
        
        print("\n🎉 Web interface test completed!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    finally:
        # Cleanup
        print("\n5. Cleaning up...")
        
        # Stop server
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("Server stopped")
        
        # Remove test video
        if os.path.exists(test_video):
            os.remove(test_video)
            print(f"Removed {test_video}")
        
        # Remove any encoded outputs
        for file in os.listdir('.'):
            if file.startswith('encoded_') and file.endswith('.mp4'):
                os.remove(file)
                print(f"Removed {file}")

if __name__ == "__main__":
    test_web_interface()
