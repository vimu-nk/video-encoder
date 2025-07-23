#!/usr/bin/env python3
"""
Test the fixed FFmpeg worker
"""

import sys
import os
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ffmpeg_worker import run_ffmpeg

def test_fixed_ffmpeg():
    """Test the fixed FFmpeg functionality"""
    
    print("Testing Fixed FFmpeg Worker")
    print("=" * 30)
    
    # Create a test video
    print("\n1. Creating test video...")
    test_input = "test_video.mp4"
    test_output = "encoded_output.mp4"
    
    # Create a simple 10-second test video
    create_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=10:size=1280x720:rate=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", "10",
        test_input
    ]
    
    print(f"Creating: {' '.join(create_cmd)}")
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create test video: {result.stderr}")
        return
    
    print("✅ Test video created successfully")
    
    # Test our fixed run_ffmpeg function
    print("\n2. Testing fixed run_ffmpeg function...")
    
    def progress_callback(percent):
        if percent % 10 == 0 or percent > 95:  # Print every 10% and final stages
            print(f"Progress: {percent}%")
    
    try:
        return_code = run_ffmpeg(
            input_path=test_input,
            output_path=test_output,
            progress_callback=progress_callback,
            preset_name="fast"
        )
        
        if return_code == 0:
            print("✅ FFmpeg encoding completed successfully!")
            
            # Check if output file exists and has content
            if os.path.exists(test_output):
                size = os.path.getsize(test_output)
                print(f"✅ Output file created: {test_output} ({size} bytes)")
                
                # Get video info
                info_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", test_output]
                info_result = subprocess.run(info_cmd, capture_output=True, text=True)
                
                if info_result.returncode == 0:
                    import json
                    data = json.loads(info_result.stdout)
                    duration = float(data["format"]["duration"])
                    video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
                    if video_stream:
                        codec = video_stream["codec_name"]
                        width = video_stream["width"]
                        height = video_stream["height"]
                        print(f"✅ Video info: {codec} {width}x{height}, duration: {duration:.2f}s")
            else:
                print("❌ Output file not created")
        else:
            print(f"❌ FFmpeg failed with return code: {return_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test different presets
    print("\n3. Testing different presets...")
    presets_to_test = ["ultrafast", "fast", "medium"]
    
    for preset in presets_to_test:
        preset_output = f"test_{preset}_output.mp4"
        print(f"\nTesting preset: {preset}")
        
        try:
            return_code = run_ffmpeg(
                input_path=test_input,
                output_path=preset_output,
                progress_callback=None,  # No progress for faster testing
                preset_name=preset
            )
            
            if return_code == 0 and os.path.exists(preset_output):
                size = os.path.getsize(preset_output)
                print(f"✅ {preset} preset works ({size} bytes)")
                os.remove(preset_output)  # Clean up
            else:
                print(f"❌ {preset} preset failed with return code: {return_code}")
                
        except Exception as e:
            print(f"❌ {preset} preset error: {str(e)}")
    
    # Cleanup
    print("\n4. Cleaning up...")
    for file in [test_input, test_output]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_fixed_ffmpeg()
