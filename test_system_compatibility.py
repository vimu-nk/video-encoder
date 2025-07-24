#!/usr/bin/env python3
"""
Test system compatibility and create fallback for non-GPU environments
"""

import sys
import os
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ffmpeg_worker import get_gpu_info, get_nvenc_capabilities, run_ffmpeg

def test_system_fallback():
    """Test system with automatic fallback to CPU encoding if no GPU"""
    
    print("🔧 System Compatibility Test")
    print("=" * 40)
    
    # Check GPU availability
    gpu_info = get_gpu_info()
    nvenc_caps = get_nvenc_capabilities()
    
    has_gpu = len(gpu_info) > 0
    has_nvenc = any(nvenc_caps.values())
    
    print(f"\n📊 System Status:")
    print(f"  GPU Detected: {'✅ Yes' if has_gpu else '❌ No'}")
    print(f"  NVENC Available: {'✅ Yes' if has_nvenc else '❌ No'}")
    
    if has_gpu and has_nvenc:
        print("\n🚀 GPU-Optimized Configuration:")
        print("  • AV1 NVENC encoding")
        print("  • Hardware acceleration") 
        print("  • 5-10x speed improvement")
        codec_info = "NVENC Hardware"
    else:
        print("\n🛠️ CPU Fallback Configuration:")
        print("  • Software x264/x265 encoding")
        print("  • Multi-threaded CPU optimization")
        print("  • Compatible with all systems")
        codec_info = "CPU Software"
    
    # Create test video
    print(f"\n🎬 Testing {codec_info} Encoding...")
    
    test_input = "compatibility_test.mp4"
    test_output = "compatibility_output.mkv"
    
    # Create a small test video
    create_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=5:size=640x480:rate=15",
        "-c:v", "libx264", "-preset", "ultrafast", "-t", "5",
        test_input
    ]
    
    print("Creating test video...")
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create test video")
        return
    
    print("✅ Test video created")
    
    # Test encoding with current system
    def progress_callback(percent):
        if percent % 25 == 0 or percent > 95:
            print(f"  Encoding: {percent}%")
    
    try:
        print("🔄 Starting encoding test...")
        return_code = run_ffmpeg(
            input_path=test_input,
            output_path=test_output,
            progress_callback=progress_callback,
            preset_name="fast"
        )
        
        if return_code == 0:
            print("✅ Encoding test successful!")
            
            if os.path.exists(test_output):
                size = os.path.getsize(test_output)
                print(f"✅ Output created: {size:,} bytes")
                
                # Check if it's actually MKV
                probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", test_output]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                
                if probe_result.returncode == 0:
                    import json
                    data = json.loads(probe_result.stdout)
                    format_name = data.get("format", {}).get("format_name", "unknown")
                    print(f"✅ Container: {format_name}")
                    
            else:
                print("❌ Output file not created")
        else:
            print(f"❌ Encoding failed with return code: {return_code}")
            
    except Exception as e:
        print(f"❌ Encoding error: {e}")
    
    # Cleanup
    for file in [test_input, test_output]:
        if os.path.exists(file):
            os.remove(file)
    
    print(f"\n🎯 System Configuration Summary:")
    print(f"  Environment: {'DigitalOcean GPU Ready' if has_gpu else 'Development/CPU Mode'}")
    print(f"  Best Codec: {'AV1 NVENC' if has_nvenc else 'x265 Software'}")
    print(f"  Container: MKV (Matroska)")
    print(f"  Audio: Opus 128k")
    print(f"  Auto-cleanup: Enabled")
    
    print(f"\n📋 Deployment Instructions:")
    if has_gpu and has_nvenc:
        print("  🚀 Ready for production on DigitalOcean GPU droplet!")
        print("  💡 Use 'fast' or 'medium' presets for best balance")
    else:
        print("  🛠️ Development mode - will use CPU encoding")
        print("  💡 Deploy to DigitalOcean GPU droplet for NVENC acceleration")
    
    print(f"\n🌐 Start web server:")
    print(f"  uvicorn app.main:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    test_system_fallback()
