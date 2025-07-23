#!/usr/bin/env python3
"""
Test script for x265 bitrate-based encoding
"""

from app.ffmpeg_worker import get_ffmpeg_preset, get_resolution_bitrates, detect_resolution

def test_bitrate_system():
    """Test the new x265 bitrate-based encoding system"""
    print("X265 Bitrate-Based Encoding System")
    print("=" * 50)
    
    # Test resolution bitrates
    bitrates = get_resolution_bitrates()
    print("\nResolution-Based Bitrates:")
    for resolution, bitrate in bitrates.items():
        mb_rate = float(bitrate.rstrip('k')) / 1000
        print(f"  {resolution:>6}: {bitrate:>6} ({mb_rate:.1f} MB/s)")
    
    # Test presets 
    print("\nX265 Encoding Presets:")
    presets = ["ultrafast", "superfast", "veryfast", "fast", "medium", "slow_hq"]
    
    for preset_name in presets:
        config = get_ffmpeg_preset(preset_name)
        quality_info = {
            "ultrafast": "⚡ Fastest x265 encoding",
            "superfast": "🚀 Very fast x265 encoding",
            "veryfast": "⚡ Fast x265 encoding", 
            "fast": "✅ Recommended x265 balance",
            "medium": "⚖️ Balanced x265 quality",
            "slow_hq": "🎯 Highest quality x265 (10-bit)"
        }
        
        print(f"\n{preset_name.upper()}:")
        print(f"  Codec: {config['codec']}")
        print(f"  Preset: {config['preset']}")
        print(f"  Format: {config['pix_fmt']}")
        print(f"  Info: {quality_info.get(preset_name, 'Unknown')}")
        if config['extra_args']:
            print(f"  Extra: {' '.join(config['extra_args'])}")
    
    print("\nKey Changes from Previous Version:")
    print("• Switched from x264 to x265 for better compression")
    print("• Using bitrate instead of CRF for consistent file sizes")
    print("• Resolution auto-detection with appropriate bitrates")
    print("• AAC audio encoding for better compatibility")
    print("• Buffer size management for stable bitrates")

def simulate_encoding_command(resolution="1080p", preset="fast"):
    """Simulate the FFmpeg command that would be generated"""
    bitrates = get_resolution_bitrates()
    target_bitrate = bitrates[resolution]
    preset_config = get_ffmpeg_preset(preset)
    
    print(f"\nSimulated FFmpeg Command for {resolution} with {preset} preset:")
    print("-" * 60)
    
    command_parts = [
        "ffmpeg",
        "-i input_video.mp4",
        f"-c:v {preset_config['codec']}",
        f"-preset {preset_config['preset']}", 
        f"-b:v {target_bitrate}",
        f"-maxrate {target_bitrate}",
        f"-bufsize {int(target_bitrate.rstrip('k')) * 2}k",
        f"-pix_fmt {preset_config['pix_fmt']}",
        "-c:a aac",
        "-b:a 128k",
        "-movflags +faststart",
        "-threads 0",
        "-y output_video.mp4"
    ]
    
    print(" \\\n  ".join(command_parts))

if __name__ == "__main__":
    test_bitrate_system()
    simulate_encoding_command("1080p", "fast") 
    simulate_encoding_command("720p", "medium")
