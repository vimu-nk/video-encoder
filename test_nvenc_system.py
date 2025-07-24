#!/usr/bin/env python3
"""
Test NVENC-optimized video encoder system for DigitalOcean GPU droplet
"""

import sys
import os
import subprocess
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ffmpeg_worker import get_gpu_info, get_nvenc_capabilities, get_cpu_info, get_optimal_settings_for_resolution

def test_nvenc_system():
    """Test the NVENC-optimized encoding system"""
    
    print("🚀 NVENC Video Encoder System Test")
    print("=" * 50)
    
    # Test GPU detection
    print("\n1. 🖥️ Testing GPU Detection:")
    gpu_info = get_gpu_info()
    if gpu_info:
        for i, gpu in enumerate(gpu_info):
            print(f"  ✅ GPU {i}: {gpu['name']}")
            print(f"     💾 Memory: {gpu['memory']:,} MB")
            print(f"     🔧 Driver: {gpu['driver']}")
    else:
        print("  ❌ No GPU detected or nvidia-smi not available")
    
    # Test NVENC capabilities
    print("\n2. ⚡ Testing NVENC Capabilities:")
    nvenc_caps = get_nvenc_capabilities()
    for codec, available in nvenc_caps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {codec}: {'Available' if available else 'Not Available'}")
    
    # Test CPU info
    print("\n3. 🧠 Testing CPU Configuration:")
    cpu_info = get_cpu_info()
    print(f"  ✅ CPU cores: {cpu_info['cpu_count']}")
    print(f"  ✅ Optimal threads: {cpu_info['optimal_threads']}")
    
    # Test optimal settings
    print("\n4. 🎯 Testing Optimal Settings:")
    optimal_settings = get_optimal_settings_for_resolution()
    for resolution, settings in optimal_settings.items():
        print(f"  ✅ {resolution}: CRF {settings['crf']}, Max: {settings['max_bitrate']}, Buffer: {settings['buffer']}")
    
    # Test FFmpeg NVENC availability
    print("\n5. 🔧 Testing FFmpeg NVENC Support:")
    try:
        result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout
            encoders = {
                'av1_nvenc': 'av1_nvenc' in output,
                'hevc_nvenc': 'hevc_nvenc' in output,
                'h264_nvenc': 'h264_nvenc' in output
            }
            for encoder, available in encoders.items():
                status = "✅" if available else "❌"
                print(f"  {status} {encoder}: {'Available' if available else 'Not Available'}")
        else:
            print("  ❌ FFmpeg not found or error occurred")
    except Exception as e:
        print(f"  ❌ Error testing FFmpeg: {e}")
    
    # Test system readiness
    print("\n6. 🎉 System Readiness Check:")
    
    # Check if we have GPU + NVENC
    has_gpu = len(gpu_info) > 0
    has_nvenc = nvenc_caps.get('av1_nvenc', False) or nvenc_caps.get('hevc_nvenc', False)
    
    if has_gpu and has_nvenc:
        print("  ✅ NVIDIA GPU detected")
        print("  ✅ NVENC hardware acceleration available")
        print("  ✅ System optimized for GPU encoding")
        print("  🚀 Ready for ultra-fast AV1/HEVC encoding!")
        
        # Recommend best preset
        if nvenc_caps.get('av1_nvenc', False):
            print("  🎯 Recommended: AV1 NVENC for best compression")
        elif nvenc_caps.get('hevc_nvenc', False):
            print("  🎯 Recommended: HEVC NVENC for good compression")
        else:
            print("  🎯 Recommended: H.264 NVENC for compatibility")
            
        print("\n🔥 PERFORMANCE BENEFITS:")
        print("  • 5-10x faster encoding than CPU")
        print("  • Lower power consumption")
        print("  • Real-time encoding possible")
        print("  • Automatic cleanup of source files")
        print("  • MKV container with Opus audio")
        
    else:
        print("  ⚠️ NVENC not available - falling back to CPU encoding")
        print("  💡 For best performance, ensure NVIDIA drivers are installed")
    
    print("\n📊 Optimization Summary:")
    print(f"  • Container: MKV (Matroska)")
    print(f"  • Video Codec: AV1/HEVC NVENC")
    print(f"  • Audio Codec: Opus 128k")
    print(f"  • Rate Control: CRF (quality-based)")
    print(f"  • Hardware Acceleration: CUDA")
    print(f"  • Auto Cleanup: Enabled")
    print(f"  • CPU Threads: {cpu_info['optimal_threads']}")

def create_nvenc_test_video():
    """Create a test video and encode with NVENC"""
    print("\n🎬 Creating test video for NVENC encoding...")
    
    # Create test video
    test_input = "nvenc_test_input.mp4"
    test_output = "nvenc_test_output.mkv"
    
    create_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=10:size=1920x1080:rate=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", "10",
        test_input
    ]
    
    print("Creating test video...")
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create test video: {result.stderr}")
        return
    
    print("✅ Test video created")
    
    # Test NVENC encoding
    from app.ffmpeg_worker import run_ffmpeg
    
    print("🚀 Testing NVENC encoding...")
    
    def progress_callback(percent):
        if percent % 20 == 0 or percent > 95:
            print(f"  Encoding progress: {percent}%")
    
    try:
        return_code = run_ffmpeg(
            input_path=test_input,
            output_path=test_output,
            progress_callback=progress_callback,
            preset_name="fast"
        )
        
        if return_code == 0:
            print("✅ NVENC encoding test successful!")
            
            # Check output file
            if os.path.exists(test_output):
                size = os.path.getsize(test_output)
                print(f"✅ Output MKV created: {size:,} bytes")
                
                # Check if original was cleaned up (should be removed by run_ffmpeg)
                if not os.path.exists(test_input):
                    print("✅ Original file automatically cleaned up")
                else:
                    print("⚠️ Original file not cleaned up")
                    
            else:
                print("❌ Output file not created")
                
        else:
            print(f"❌ NVENC encoding failed with return code: {return_code}")
            
    except Exception as e:
        print(f"❌ NVENC test error: {e}")
    
    # Cleanup
    for file in [test_input, test_output]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up: {file}")

if __name__ == "__main__":
    test_nvenc_system()
    
    # Ask if user wants to run encoding test
    print("\n" + "="*50)
    choice = input("🎬 Run NVENC encoding test? (y/N): ").lower().strip()
    if choice in ['y', 'yes']:
        create_nvenc_test_video()
    
    print("\n🎉 Testing completed!")
    print("\nTo start the web server:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nFor production:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1")
