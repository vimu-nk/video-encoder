#!/usr/bin/env python3
"""
Simple NVENC detection test for DigitalOcean deployment
"""
from app.ffmpeg_worker import get_nvenc_capabilities, get_ffmpeg_preset

print("🔍 NVENC Detection Test")
print("=" * 40)

# Test NVENC capabilities
nvenc_caps = get_nvenc_capabilities()
print(f"NVENC Capabilities: {nvenc_caps}")

# Test if NVENC will be used
has_nvenc = any(nvenc_caps.values())
print(f"Will use NVENC: {has_nvenc}")

if has_nvenc:
    # Test preset selection
    preset = get_ffmpeg_preset("fast")
    print(f"Selected codec: {preset['codec']}")
    print(f"Preset: {preset['preset']}")
    
    if nvenc_caps.get('av1_nvenc'):
        print("✅ AV1 NVENC will be used")
    elif nvenc_caps.get('hevc_nvenc'):
        print("✅ HEVC NVENC will be used")  
    else:
        print("✅ H.264 NVENC will be used")
else:
    print("❌ CPU fallback will be used")

print("✅ Test complete")
