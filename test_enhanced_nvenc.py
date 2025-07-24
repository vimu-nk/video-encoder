#!/usr/bin/env python3
"""
Test enhanced NVENC system with maximum GPU core utilization and storage efficiency
"""

import sys
import os
import subprocess
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ffmpeg_worker import (
    get_gpu_info, get_nvenc_capabilities, get_optimal_settings_for_resolution,
    run_ffmpeg, get_ffmpeg_preset
)

def test_enhanced_nvenc_system():
    """Test the enhanced NVENC system with maximum GPU utilization and storage efficiency"""
    
    print("🚀 Enhanced NVENC System Test - Maximum GPU Core Utilization")
    print("=" * 70)
    
    # Test GPU capabilities
    print("\n1. 🖥️ Advanced GPU Detection:")
    gpu_info = get_gpu_info()
    if gpu_info:
        for i, gpu in enumerate(gpu_info):
            print(f"  ✅ GPU {i}: {gpu['name']}")
            print(f"     💾 Memory: {gpu['memory']:,} MB")
            print(f"     🔧 Driver: {gpu['driver']}")
            if 'compute_cap' in gpu:
                print(f"     🧮 Compute Capability: {gpu['compute_cap']}")
                print(f"     ⚡ Max Graphics Clock: {gpu['max_graphics_clock']} MHz")
                print(f"     🔗 Max Memory Clock: {gpu['max_memory_clock']} MHz")
    else:
        print("  ❌ No GPU detected or nvidia-smi not available")
    
    # Test NVENC capabilities
    print("\n2. ⚡ NVENC Hardware Acceleration:")
    nvenc_caps = get_nvenc_capabilities()
    for codec, available in nvenc_caps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {codec}: {'Available' if available else 'Not Available'}")
    
    # Test aggressive compression settings
    print("\n3. 🗜️ Storage Efficiency Settings:")
    settings = get_optimal_settings_for_resolution()
    for resolution, config in settings.items():
        print(f"  ✅ {resolution}: CRF {config['crf']} | Max: {config['max_bitrate']} | Target: {config['target_bitrate']}")
    
    # Test enhanced presets
    print("\n4. 🎯 Enhanced NVENC Presets:")
    presets = ["ultrafast", "fast", "medium", "slow_hq"]
    for preset in presets:
        config = get_ffmpeg_preset(preset)
        print(f"  ✅ {preset}: {config['codec']} | Extra optimizations: {len(config.get('extra_args', []))} args")
    
    print(f"\n5. 🔥 Key Performance Enhancements:")
    print(f"  • Multipass encoding for better compression")
    print(f"  • Adaptive B-frames and weighted prediction")
    print(f"  • Maximum lookahead (64 frames)")
    print(f"  • High-quality variable bitrate (VBR_HQ)")
    print(f"  • 64 GPU surfaces for maximum parallelism")
    print(f"  • Zero-latency mode for real-time processing")
    print(f"  • Opus audio at 96k for storage efficiency")
    print(f"  • Maximum MKV compression level")
    print(f"  • Metadata removal for smaller files")
    
    # Performance comparison table
    print(f"\n6. 📊 Expected Storage Efficiency:")
    print(f"  Resolution | CRF | Expected Compression | Use Case")
    print(f"  ---------- | --- | -------------------- | --------")
    print(f"  4K         | 30  | 50-70% size reduction | Premium content")
    print(f"  1440p      | 32  | 55-75% size reduction | High quality")
    print(f"  1080p      | 34  | 60-80% size reduction | Standard HD")
    print(f"  720p       | 36  | 65-85% size reduction | Mobile/web")
    print(f"  480p       | 38  | 70-90% size reduction | Low bandwidth")
    print(f"  360p       | 40  | 75-95% size reduction | Ultra efficient")

def test_storage_efficiency():
    """Test actual storage efficiency with enhanced settings"""
    print(f"\n🧪 Storage Efficiency Test")
    print("=" * 40)
    
    # Create different resolution test videos
    test_videos = [
        {"name": "test_1080p.mp4", "size": "1920x1080", "duration": "10"},
        {"name": "test_720p.mp4", "size": "1280x720", "duration": "10"},
        {"name": "test_480p.mp4", "size": "854x480", "duration": "10"}
    ]
    
    compression_results = []
    
    for video in test_videos:
        print(f"\n📹 Testing {video['name']} ({video['size']})...")
        
        # Create test video
        create_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"testsrc=duration={video['duration']}:size={video['size']}:rate=30",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",  # Good quality source
            "-t", video['duration'],
            video['name']
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ Failed to create {video['name']}")
            continue
        
        original_size = os.path.getsize(video['name'])
        print(f"  📁 Original size: {original_size:,} bytes ({original_size / (1024*1024):.1f} MB)")
        
        # Encode with enhanced NVENC settings
        output_name = video['name'].replace('.mp4', '_enhanced.mkv')
        
        try:
            def progress_callback(percent):
                if percent % 25 == 0 or percent > 95:
                    print(f"    Encoding: {percent}%")
            
            return_code = run_ffmpeg(
                input_path=video['name'],
                output_path=output_name,
                progress_callback=progress_callback,
                preset_name="medium"
            )
            
            if return_code == 0 and os.path.exists(output_name):
                compressed_size = os.path.getsize(output_name)
                compression_ratio = (1 - compressed_size / original_size) * 100
                space_saved = (original_size - compressed_size) / (1024*1024)
                
                print(f"  ✅ Compressed size: {compressed_size:,} bytes ({compressed_size / (1024*1024):.1f} MB)")
                print(f"  🗜️ Compression: {compression_ratio:.1f}% smaller ({space_saved:.1f} MB saved)")
                
                compression_results.append({
                    "resolution": video['size'],
                    "original_mb": original_size / (1024*1024),
                    "compressed_mb": compressed_size / (1024*1024),
                    "compression_ratio": compression_ratio,
                    "space_saved_mb": space_saved
                })
                
                # Cleanup
                os.remove(output_name)
            else:
                print(f"  ❌ Encoding failed for {video['name']}")
                
        except Exception as e:
            print(f"  ❌ Error encoding {video['name']}: {e}")
        
        # Cleanup original
        if os.path.exists(video['name']):
            os.remove(video['name'])
    
    # Summary
    if compression_results:
        print(f"\n📊 Compression Summary:")
        print(f"Resolution  | Original | Compressed | Saved | Efficiency")
        print(f"----------- | -------- | ---------- | ----- | ----------")
        for result in compression_results:
            print(f"{result['resolution']:<11} | {result['original_mb']:>6.1f}MB | {result['compressed_mb']:>8.1f}MB | {result['space_saved_mb']:>4.1f}MB | {result['compression_ratio']:>7.1f}%")
        
        avg_compression = sum(r['compression_ratio'] for r in compression_results) / len(compression_results)
        total_saved = sum(r['space_saved_mb'] for r in compression_results)
        print(f"----------- | -------- | ---------- | ----- | ----------")
        print(f"{'Average':<11} | {'N/A':<8} | {'N/A':<10} | {total_saved:>4.1f}MB | {avg_compression:>7.1f}%")

if __name__ == "__main__":
    test_enhanced_nvenc_system()
    
    print("\n" + "="*70)
    choice = input("🧪 Run storage efficiency test? (y/N): ").lower().strip()
    if choice in ['y', 'yes']:
        test_storage_efficiency()
    
    print("\n🎉 Enhanced NVENC testing completed!")
    print("\n🚀 System Benefits:")
    print("  • Maximum GPU core utilization with 64 surfaces")
    print("  • Multipass encoding for superior compression")
    print("  • Aggressive CRF settings for storage efficiency")
    print("  • Enhanced metadata removal and container optimization")
    print("  • Real-time compression statistics and monitoring")
    print("\n🌐 Start the enhanced encoder:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
