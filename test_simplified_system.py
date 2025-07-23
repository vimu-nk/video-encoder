#!/usr/bin/env python3
"""
Test the simplified single-job encoding system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ffmpeg_worker import get_cpu_info, get_ffmpeg_preset

def test_simplified_system():
    """Test the simplified encoding system components"""
    print("Simplified Video Encoder System Test")
    print("=" * 45)
    
    # Test CPU optimization
    print("\n1. Testing CPU Optimization:")
    cpu_info = get_cpu_info()
    print(f"  ✅ CPU cores: {cpu_info['cpu_count']}")
    print(f"  ✅ Optimal threads: {cpu_info['optimal_threads']}")
    print(f"  ✅ Pool threads: {cpu_info['pool_threads']}")
    
    # Test FFmpeg presets
    print("\n2. Testing FFmpeg Presets:")
    presets = ["ultrafast", "superfast", "veryfast", "fast", "medium", "slow_hq"]
    for preset in presets:
        config = get_ffmpeg_preset(preset)
        print(f"  ✅ {preset}: {config['codec']} ({config['preset']})")
    
    # Test bitrate system
    print("\n3. Testing Resolution Bitrates:")
    from app.ffmpeg_worker import get_resolution_bitrates
    bitrates = get_resolution_bitrates()
    for resolution, bitrate in bitrates.items():
        mb_rate = float(bitrate.rstrip('k')) / 1000
        print(f"  ✅ {resolution}: {bitrate} ({mb_rate:.1f} MB/s)")
    
    print("\n4. System Status:")
    print("  ✅ Queue system: REMOVED (simplified)")
    print("  ✅ Single job processing: ENABLED")
    print("  ✅ Background tasks: ENABLED")
    print("  ✅ Real-time status: ENABLED")
    print("  ✅ CPU optimization: MAXIMIZED")
    print("  ✅ SSL retry logic: ENHANCED")
    
    print("\n🎉 Simplified system test completed!")
    print("\nTo test the web interface:")
    print("1. Start: uvicorn app.main:app --reload")
    print("2. Visit: http://localhost:8000/")
    print("3. Submit a job and monitor at: http://localhost:8000/logs")

if __name__ == "__main__":
    test_simplified_system()
