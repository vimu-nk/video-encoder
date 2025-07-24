# 🚀 NVENC-Optimized Video Encoder for DigitalOcean GPU Droplet

## 🎯 Overview

This system is now **fully optimized** for DigitalOcean GPU droplets with **NVIDIA RTX 4000 ADA** graphics cards, utilizing NVENC hardware acceleration for blazing-fast AV1/HEVC encoding.

## ⚡ Key Optimizations

### 🖥️ Hardware Acceleration

-   **NVENC AV1**: Primary codec for maximum compression efficiency
-   **NVENC HEVC**: Fallback for broad compatibility
-   **CUDA acceleration**: GPU-based decode/encode pipeline
-   **RTX 4000 ADA optimized**: 64 surfaces, variable bitrate control

### 📦 Container & Codecs

-   **Container**: MKV (Matroska) - optimal for streaming and quality
-   **Video**: AV1 NVENC (primary) / HEVC NVENC (fallback)
-   **Audio**: Opus 128k - superior quality/compression vs AAC
-   **Rate Control**: CRF (Constant Rate Factor) for quality-based encoding

### 🎚️ Quality Settings by Resolution

| Resolution | CRF | Max Bitrate | Target Bitrate | Buffer Size |
| ---------- | --- | ----------- | -------------- | ----------- |
| **4K**     | 28  | 8,000k      | 6,000k         | 12,000k     |
| **1440p**  | 30  | 4,000k      | 3,000k         | 6,000k      |
| **1080p**  | 32  | 2,500k      | 2,000k         | 5,000k      |
| **720p**   | 34  | 1,500k      | 1,200k         | 3,000k      |
| **480p**   | 36  | 800k        | 600k           | 1,600k      |
| **360p**   | 38  | 500k        | 400k           | 1,000k      |

### 🏃‍♂️ Performance Presets

| Preset    | NVENC Preset | Tune | Features                           |
| --------- | ------------ | ---- | ---------------------------------- |
| ultrafast | p1           | ll   | Low latency, basic quality         |
| superfast | p2           | ll   | Low latency, improved quality      |
| veryfast  | p3           | hq   | High quality, fast encoding        |
| fast      | p4           | hq   | Balanced quality/speed + lookahead |
| medium    | p5           | hq   | Better quality + longer lookahead  |
| slow_hq   | p6           | hq   | Maximum quality + B-frame refs     |

## 🔧 System Requirements

### DigitalOcean GPU Droplet

-   **GPU**: NVIDIA RTX 4000 ADA (recommended)
-   **VRAM**: 16GB+ recommended for 4K encoding
-   **CPU**: 8+ cores for optimal performance
-   **RAM**: 16GB+ recommended
-   **Storage**: SSD for temporary file operations

### Software Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ffmpeg nvidia-driver-535 nvidia-utils-535

# Verify NVENC support
ffmpeg -encoders | grep nvenc
nvidia-smi
```

## 🚀 Performance Benefits

### Speed Improvements

-   **5-10x faster** than CPU encoding
-   **Real-time encoding** possible for 1080p content
-   **Parallel processing** with GPU + CPU tasks
-   **Instant startup** - no warmup time needed

### Efficiency Gains

-   **Lower power consumption** vs CPU encoding
-   **Reduced heat generation**
-   **Background encoding** without impacting system performance
-   **Automatic cleanup** of source files to save storage

### Quality Advantages

-   **AV1 codec**: 30% better compression than HEVC
-   **CRF encoding**: Consistent quality across content types
-   **Adaptive quality**: Automatic resolution detection
-   **Opus audio**: Superior to AAC at same bitrates

## 📊 Encoding Workflow

### 1. File Upload

```
📥 Download from storage → 📍 Local input folder
```

### 2. Hardware Detection

```
🖥️ Detect GPU → ⚡ Check NVENC caps → 🎯 Select optimal codec
```

### 3. NVENC Encoding

```
🚀 CUDA decode → ⚡ NVENC encode → 📦 MKV container
```

### 4. Storage & Cleanup

```
📤 Upload MKV → 🗑️ Auto-cleanup source files
```

## 🎮 Usage Examples

### Web Interface

```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Access dashboard
http://your-droplet-ip:8000/

# Monitor jobs
http://your-droplet-ip:8000/logs
```

### Direct API

```bash
# Upload and encode
curl -X POST "http://your-droplet-ip:8000/upload" \
  -F "file=@video.mp4" \
  -F "quality=fast" \
  -F "upload_to_bunny=true"

# Check status
curl "http://your-droplet-ip:8000/api/status"
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Optional: Force specific codec
export NVENC_CODEC="av1_nvenc"  # or "hevc_nvenc"

# Optional: Override quality preset
export DEFAULT_PRESET="medium"

# Optional: Disable auto-cleanup
export KEEP_ORIGINALS="true"
```

### Custom Settings

Edit `app/ffmpeg_worker.py` to modify:

-   CRF values for different quality levels
-   Bitrate caps for bandwidth limitations
-   Audio codec preferences
-   Container format options

## 📈 Monitoring & Logs

### Real-time Status

-   **Web interface**: Live progress updates
-   **API endpoint**: JSON status responses
-   **Console logs**: Detailed encoding information

### Performance Metrics

-   **Encoding speed**: FPS processing rate
-   **GPU utilization**: NVENC usage percentage
-   **Memory usage**: VRAM consumption
-   **Storage savings**: Compression ratios

## 🛠️ Troubleshooting

### Common Issues

#### "NVENC not available"

```bash
# Check GPU
nvidia-smi

# Check FFmpeg NVENC support
ffmpeg -encoders | grep nvenc

# Update drivers if needed
sudo apt install nvidia-driver-535
```

#### "Encoding failed"

```bash
# Check available codecs
python test_nvenc_system.py

# Verify file permissions
ls -la input/ output/

# Check disk space
df -h
```

#### "Slow encoding"

```bash
# Verify GPU is being used
nvidia-smi

# Check preset settings
# Lower presets = faster encoding
```

## 🎉 Success Indicators

### System Ready

-   ✅ NVIDIA GPU detected
-   ✅ NVENC capabilities available
-   ✅ AV1/HEVC encoding functional
-   ✅ MKV output with Opus audio
-   ✅ Automatic file cleanup working

### Optimal Performance

-   🚀 5-10x speed improvement over CPU
-   💾 30%+ file size reduction with AV1
-   ⚡ Real-time encoding for HD content
-   🗑️ Automatic storage management
-   📊 Consistent quality across resolutions

---

## 🎯 Ready for Production!

Your DigitalOcean GPU droplet is now optimized for:

-   **Ultra-fast AV1 encoding** with NVENC
-   **MKV container** for streaming compatibility
-   **Automatic quality optimization** based on resolution
-   **Efficient storage management** with auto-cleanup
-   **24/7 operation** with background processing

Start encoding: `uvicorn app.main:app --host 0.0.0.0 --port 8000` 🚀
