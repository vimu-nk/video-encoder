# FFmpeg Encoding Optimization - X265 Bitrate System

## Updated Implementation

Changed from CRF-based encoding to **x265 with resolution-based bitrates** for consistent file sizes and predictable quality.

## New X265 Bitrate Configuration

### Resolution-Based Bitrates

-   **1080p**: 1.5 MB/s (1500k) - High quality for full HD content
-   **720p**: 1.0 MB/s (1000k) - Balanced quality for HD content
-   **480p**: 750 KB/s (750k) - Good quality for SD content
-   **360p**: 500 KB/s (500k) - Optimized for mobile/low bandwidth

### Technical Advantages

1. **Consistent File Sizes**: Bitrate encoding ensures predictable output sizes
2. **x265 Compression**: Better compression efficiency than x264 (~25-50% smaller files)
3. **Auto-Resolution Detection**: Automatically detects video resolution and applies appropriate bitrate
4. **Quality Optimization**: Bitrates chosen for optimal quality/size balance per resolution

## Preset Options (All x265)

1. **Ultra Fast** (`ultrafast`)

    - Fastest x265 encoding with fastdecode tuning
    - Best for: Quick previews, testing

2. **Super Fast** (`superfast`)

    - Very fast x265 encoding
    - Best for: Development, rapid turnaround

3. **Very Fast** (`veryfast`)

    - Fast x265 encoding with good quality
    - Best for: Regular production workflows

4. **Fast** (`fast`) - **DEFAULT & RECOMMENDED**

    - Optimal balance of speed and quality
    - Best for: Most production scenarios

5. **Medium** (`medium`)

    - Balanced x265 approach
    - Best for: Quality-focused workflows

6. **Slow HQ** (`slow_hq`)
    - Highest quality x265 with 10-bit encoding
    - Best for: Final masters, archival content

## FFmpeg Command Structure

```bash
ffmpeg -i input.mp4 \
  -c:v libx265 \
  -preset fast \
  -b:v 1500k \           # Target bitrate (resolution-based)
  -maxrate 1500k \       # Maximum bitrate cap
  -bufsize 3000k \       # Buffer size (2x bitrate)
  -pix_fmt yuv420p \     # Standard color format
  -c:a aac \             # AAC audio codec
  -b:a 128k \            # Audio bitrate
  -movflags +faststart \ # Web streaming optimization
  -threads 0 \           # Use all CPU cores
  -y output.mp4
```

## Benefits Over Previous CRF System

### File Size Predictability

-   **Before**: CRF produced variable file sizes depending on content complexity
-   **After**: Bitrate ensures consistent, predictable file sizes

### Quality Consistency

-   **Before**: Quality varied based on scene complexity
-   **After**: Consistent quality across different content types

### Compression Efficiency

-   **Before**: x264 codec with moderate compression
-   **After**: x265 codec with superior compression (25-50% smaller files)

### Resolution Optimization

-   **Before**: One-size-fits-all encoding settings
-   **After**: Optimized bitrates per resolution for best quality/size ratio

## Production Ready Features

✅ **Automatic Resolution Detection** - Uses ffprobe to detect input resolution  
✅ **Optimized Bitrate Selection** - Applies appropriate bitrate automatically  
✅ **x265 Compression** - Superior compression efficiency  
✅ **AAC Audio** - Better audio compatibility than copy  
✅ **Web Streaming** - Faststart flag for progressive download  
✅ **Multi-threading** - Uses all available CPU cores  
✅ **Buffer Management** - Stable bitrate control with proper buffering

## Deployment Ready

The encoder now provides:

-   **Predictable file sizes** for storage planning
-   **Consistent quality** across different content types
-   **Superior compression** with x265 codec
-   **Resolution-optimized** encoding automatically applied
-   **Production-grade** settings for professional workflows
