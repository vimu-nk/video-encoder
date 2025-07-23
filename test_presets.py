#!/usr/bin/env python3
"""
Test script to compare FFmpeg encoding presets
"""

from app.ffmpeg_worker import get_ffmpeg_preset

def compare_presets():
    """Display all available presets and their settings"""
    presets = ["ultrafast", "superfast", "veryfast", "fast", "medium", "slow_hq"]
    
    print("FFmpeg Encoding Presets Comparison:")
    print("=" * 60)
    
    for preset_name in presets:
        config = get_ffmpeg_preset(preset_name)
        speed_info = {
            "ultrafast": "⚡ Fastest encoding, lowest quality",
            "superfast": "🚀 Very fast encoding, good for quick tests", 
            "veryfast": "⚡ Fast encoding, decent quality",
            "fast": "✅ Recommended balance of speed/quality",
            "medium": "⚖️ Balanced speed and quality",
            "slow_hq": "🎯 Slowest but highest quality (H.265)"
        }
        
        print(f"\n{preset_name.upper()}:")
        print(f"  Codec: {config['codec']}")
        print(f"  Preset: {config['preset']}")
        print(f"  CRF: {config['crf']}")
        print(f"  Format: {config['pix_fmt']}")
        print(f"  Speed: {speed_info.get(preset_name, 'Unknown')}")
        if config['extra_args']:
            print(f"  Extra: {' '.join(config['extra_args'])}")

if __name__ == "__main__":
    compare_presets()
