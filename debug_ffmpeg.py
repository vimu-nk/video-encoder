#!/usr/bin/env python3
"""
Debug FFmpeg issues with error code 234
"""

import sys
import os
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ffmpeg_worker import get_cpu_info, get_ffmpeg_preset, detect_resolution, get_resolution_bitrates

def test_ffmpeg_command():
    """Test a simplified FFmpeg command to isolate the issue"""
    
    print("FFmpeg Debug Test")
    print("=" * 30)
    
    # Create a simple test video first
    print("\n1. Creating test video...")
    test_input = "test_input.mp4"
    test_output = "test_output.mp4"
    
    # Create a simple 5-second test video
    create_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=5:size=1280x720:rate=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", "5",
        test_input
    ]
    
    print(f"Creating test video: {' '.join(create_cmd)}")
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create test video: {result.stderr}")
        return
    
    print("✅ Test video created successfully")
    
    # Test basic FFmpeg functionality
    print("\n2. Testing basic x265 encoding...")
    
    cpu_info = get_cpu_info()
    print(f"CPU Info: {cpu_info}")
    
    # Try the simplest possible x265 command first
    simple_cmd = [
        "ffmpeg", "-y",
        "-i", test_input,
        "-c:v", "libx265",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "copy",
        "simple_output.mp4"
    ]
    
    print(f"Simple command: {' '.join(simple_cmd)}")
    result = subprocess.run(simple_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Simple x265 encoding failed with code {result.returncode}")
        print(f"Error: {result.stderr}")
        
        # Try with libx264 instead
        print("\n3. Testing with libx264...")
        x264_cmd = [
            "ffmpeg", "-y",
            "-i", test_input,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",
            "x264_output.mp4"
        ]
        
        print(f"x264 command: {' '.join(x264_cmd)}")
        result = subprocess.run(x264_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ libx264 encoding works fine")
            print("❌ Issue is specifically with libx265")
        else:
            print(f"❌ x264 also failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
    else:
        print("✅ Simple x265 encoding works")
        
        # Now test our complex command
        print("\n4. Testing complex command...")
        resolution_category, actual_resolution = detect_resolution(test_input)
        bitrates = get_resolution_bitrates()
        target_bitrate = bitrates[resolution_category]
        preset_config = get_ffmpeg_preset("fast")
        
        complex_cmd = [
            "ffmpeg", "-y",
            "-i", test_input,
            
            # Hardware acceleration
            "-hwaccel", "auto",
            "-hwaccel_output_format", "auto",
            
            # Video encoding
            "-c:v", preset_config["codec"],
            "-preset", preset_config["preset"],
            "-b:v", target_bitrate,
            "-maxrate", target_bitrate,
            "-bufsize", f"{int(target_bitrate.rstrip('k')) * 2}k",
            "-pix_fmt", preset_config["pix_fmt"],
            
            # Audio
            "-c:a", "aac",
            "-b:a", "128k",
            
            # Threading
            "-threads", str(cpu_info["optimal_threads"]),
            "-thread_type", "frame+slice",
            "-slices", str(cpu_info["cpu_count"]),
            "-filter_complex_threads", str(cpu_info["cpu_count"]),
            
            # Optimizations
            "-movflags", "+faststart",
            "-avoid_negative_ts", "make_zero",
            "-fflags", "+genpts",
            
            "complex_output.mp4"
        ]
        
        # Add x265 params if using x265
        if preset_config["codec"] == "libx265":
            x265_params = f"pools={cpu_info['pool_threads']}:frame-threads={cpu_info['cpu_count']}:wpp:pmode:pme:asm=avx2"
            complex_cmd.insert(-1, "-x265-params")
            complex_cmd.insert(-1, x265_params)
        
        print(f"Complex command: {' '.join(complex_cmd)}")
        result = subprocess.run(complex_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Complex command failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
            
            # Try removing problematic parameters one by one
            print("\n5. Testing simplified complex command...")
            simple_complex_cmd = [
                "ffmpeg", "-y",
                "-i", test_input,
                "-c:v", "libx265",
                "-preset", "fast",
                "-b:v", "1000k",
                "-c:a", "aac",
                "-b:a", "128k",
                "-threads", "4",
                "simple_complex_output.mp4"
            ]
            
            print(f"Simplified complex: {' '.join(simple_complex_cmd)}")
            result = subprocess.run(simple_complex_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Simplified complex command works")
                print("🔍 Issue is with specific parameters in complex command")
            else:
                print(f"❌ Still failing with code {result.returncode}")
                print(f"Error: {result.stderr}")
        else:
            print("✅ Complex command works fine")
    
    # Cleanup
    print("\n6. Cleaning up test files...")
    for file in [test_input, "simple_output.mp4", "x264_output.mp4", "complex_output.mp4", "simple_complex_output.mp4"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")

if __name__ == "__main__":
    test_ffmpeg_command()
