import subprocess
import re
import os
import multiprocessing
import shutil
import json

def get_gpu_info():
    """Get GPU information for NVENC optimization"""
    try:
        # Check if nvidia-smi is available
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpu_info = []
            for line in lines:
                parts = line.split(', ')
                if len(parts) >= 3:
                    gpu_info.append({
                        'name': parts[0],
                        'memory': int(parts[1]),
                        'driver': parts[2]
                    })
            return gpu_info
        return []
    except:
        return []

def get_nvenc_capabilities():
    """Check NVENC capabilities for AV1 encoding"""
    try:
        # Check if ffmpeg supports av1_nvenc
        result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            capabilities = {
                'av1_nvenc': 'av1_nvenc' in output,
                'hevc_nvenc': 'hevc_nvenc' in output,
                'h264_nvenc': 'h264_nvenc' in output
            }
            return capabilities
        return {'av1_nvenc': False, 'hevc_nvenc': False, 'h264_nvenc': False}
    except:
        return {'av1_nvenc': False, 'hevc_nvenc': False, 'h264_nvenc': False}

def get_cpu_info():
    """Get CPU information for fallback encoding"""
    try:
        cpu_count = multiprocessing.cpu_count()
        return {
            "cpu_count": cpu_count,
            "optimal_threads": min(cpu_count, 8),  # Lower for GPU encoding
        }
    except:
        return {
            "cpu_count": 4,
            "optimal_threads": 4,
        }

def get_optimal_settings_for_resolution():
    """Get optimal CRF and bitrate settings for different resolutions with AV1 NVENC"""
    return {
        "4K": {
            "crf": 28,
            "max_bitrate": "8000k",
            "target_bitrate": "6000k",
            "buffer": "12000k"
        },
        "1440p": {
            "crf": 30,
            "max_bitrate": "4000k", 
            "target_bitrate": "3000k",
            "buffer": "6000k"
        },
        "1080p": {
            "crf": 32,
            "max_bitrate": "2500k",
            "target_bitrate": "2000k", 
            "buffer": "5000k"
        },
        "720p": {
            "crf": 34,
            "max_bitrate": "1500k",
            "target_bitrate": "1200k",
            "buffer": "3000k"
        },
        "480p": {
            "crf": 36,
            "max_bitrate": "800k",
            "target_bitrate": "600k",
            "buffer": "1600k"
        },
        "360p": {
            "crf": 38,
            "max_bitrate": "500k",
            "target_bitrate": "400k",
            "buffer": "1000k"
        }
    }

def detect_resolution(input_path):
    """Detect video resolution using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_streams", "-select_streams", "v:0", input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if data.get("streams"):
                width = data["streams"][0].get("width", 0)
                height = data["streams"][0].get("height", 0)
                
                if height >= 2160:  # 4K
                    return "4K", f"{width}x{height}"
                elif height >= 1440:  # 1440p
                    return "1440p", f"{width}x{height}"
                elif height >= 1080:
                    return "1080p", f"{width}x{height}"
                elif height >= 720:
                    return "720p", f"{width}x{height}"
                elif height >= 480:
                    return "480p", f"{width}x{height}"
                else:
                    return "360p", f"{width}x{height}"
        
        # Default fallback
        return "720p", "unknown"
        
    except Exception as e:
        print(f"Error detecting resolution: {e}")
        return "720p", "unknown"

def get_ffmpeg_preset(preset_name):
    """Get FFmpeg settings based on preset name - optimized for NVENC AV1 with CPU fallback"""
    gpu_info = get_gpu_info()
    nvenc_caps = get_nvenc_capabilities()
    
    # Check if NVENC is actually available
    has_nvenc = len(gpu_info) > 0 and any(nvenc_caps.values())
    
    # Base settings for all presets
    base_settings = {
        "container": "mkv",  # Always use MKV container
        "audio_codec": "libopus",  # Better audio codec for MKV
        "audio_bitrate": "128k"
    }
    
    if has_nvenc:
        # NVENC GPU acceleration presets
        presets = {
            "ultrafast": {
                **base_settings,
                "codec": "av1_nvenc" if nvenc_caps.get('av1_nvenc') else "hevc_nvenc",
                "preset": "p1",  # Fastest NVENC preset
                "tune": "ll",    # Low latency
                "extra_args": ["-spatial_aq", "1", "-temporal_aq", "1"]
            },
            "superfast": {
                **base_settings,
                "codec": "av1_nvenc" if nvenc_caps.get('av1_nvenc') else "hevc_nvenc",
                "preset": "p2",
                "tune": "ll",
                "extra_args": ["-spatial_aq", "1", "-temporal_aq", "1"]
            },
            "veryfast": {
                **base_settings,
                "codec": "av1_nvenc" if nvenc_caps.get('av1_nvenc') else "hevc_nvenc",
                "preset": "p3",
                "tune": "hq",    # High quality
                "extra_args": ["-spatial_aq", "1", "-temporal_aq", "1"]
            },
            "fast": {
                **base_settings,
                "codec": "av1_nvenc" if nvenc_caps.get('av1_nvenc') else "hevc_nvenc",
                "preset": "p4",
                "tune": "hq",
                "extra_args": ["-spatial_aq", "1", "-temporal_aq", "1", "-lookahead", "20"]
            },
            "medium": {
                **base_settings,
                "codec": "av1_nvenc" if nvenc_caps.get('av1_nvenc') else "hevc_nvenc",
                "preset": "p5",
                "tune": "hq",
                "extra_args": ["-spatial_aq", "1", "-temporal_aq", "1", "-lookahead", "32"]
            },
            "slow_hq": {
                **base_settings,
                "codec": "av1_nvenc" if nvenc_caps.get('av1_nvenc') else "hevc_nvenc",
                "preset": "p6",  # Highest quality NVENC preset
                "tune": "hq",
                "extra_args": ["-spatial_aq", "1", "-temporal_aq", "1", "-lookahead", "64", "-b_ref_mode", "middle"]
            }
        }
    else:
        # CPU fallback presets using x265
        print("⚠️ NVENC not available, using CPU encoding fallback")
        presets = {
            "ultrafast": {
                **base_settings,
                "codec": "libx265",
                "preset": "ultrafast",
                "extra_args": ["-tune", "fastdecode"]
            },
            "superfast": {
                **base_settings,
                "codec": "libx265", 
                "preset": "superfast",
                "extra_args": []
            },
            "veryfast": {
                **base_settings,
                "codec": "libx265",
                "preset": "veryfast", 
                "extra_args": []
            },
            "fast": {
                **base_settings,
                "codec": "libx265",
                "preset": "fast",
                "extra_args": []
            },
            "medium": {
                **base_settings,
                "codec": "libx265",
                "preset": "medium",
                "extra_args": []
            },
            "slow_hq": {
                **base_settings,
                "codec": "libx265",
                "preset": "slow",
                "extra_args": []
            }
        }
    
    return presets.get(preset_name, presets["fast"])

def run_ffmpeg(input_path, output_path, progress_callback=None, preset_name="fast"):
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create directory if there is one
        os.makedirs(output_dir, exist_ok=True)
    
    # Get system information
    cpu_info = get_cpu_info()
    gpu_info = get_gpu_info()
    nvenc_caps = get_nvenc_capabilities()
    
    # Detect video resolution and get optimal settings
    resolution_category, actual_resolution = detect_resolution(input_path)
    optimal_settings = get_optimal_settings_for_resolution()
    settings = optimal_settings[resolution_category]
    
    # Get preset configuration
    preset_config = get_ffmpeg_preset(preset_name)
    
    # Force MKV extension for output
    if not output_path.endswith('.mkv'):
        output_path = os.path.splitext(output_path)[0] + '.mkv'
    
    if progress_callback:
        progress_callback(5)  # Initial progress
    
    # Build optimized command based on available hardware
    if preset_config["codec"].endswith("_nvenc"):
        # NVENC hardware acceleration command
        command = [
            "ffmpeg",
            
            # Hardware acceleration for NVIDIA GPU
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            
            "-i", input_path,
            
            # Video encoding with NVENC
            "-c:v", preset_config["codec"],
            "-preset", preset_config["preset"],
            "-tune", preset_config["tune"],
            
            # Use CRF for quality-based encoding
            "-crf", str(settings["crf"]),
            "-maxrate", settings["max_bitrate"],
            "-bufsize", settings["buffer"],
            
            # NVENC optimizations
            "-rc", "vbr",  # Variable bitrate
            "-surfaces", "64",  # Max surfaces for modern GPUs
            "-delay", "0",  # No delay for real-time
        ]
    else:
        # CPU fallback command using x265
        command = [
            "ffmpeg",
            
            # Try hardware acceleration if available
            "-hwaccel", "auto",
            
            "-i", input_path,
            
            # Video encoding with CPU
            "-c:v", preset_config["codec"],
            "-preset", preset_config["preset"],
            
            # Use CRF for quality-based encoding
            "-crf", str(settings["crf"]),
            "-maxrate", settings["max_bitrate"],
            "-bufsize", settings["buffer"],
            
            # CPU optimizations
            "-threads", str(cpu_info["optimal_threads"]),
        ]
    
    # Common settings for both NVENC and CPU
    command.extend([
        # Audio encoding with Opus for MKV
        "-c:a", preset_config["audio_codec"],
        "-b:a", preset_config["audio_bitrate"],
        
        # Container optimizations for MKV
        "-f", "matroska",
        
        # General optimizations
        "-avoid_negative_ts", "make_zero",
    ])
    
    # Add codec-specific extra arguments
    command.extend(preset_config["extra_args"])
    
    # Add output file and overwrite flag
    command.extend(["-y", output_path])
    
    # Print encoding information
    gpu_name = gpu_info[0]['name'] if gpu_info else "No GPU"
    encoding_type = "NVENC Hardware" if preset_config["codec"].endswith("_nvenc") else "CPU Software"
    
    print(f"🚀 {encoding_type} Encoding: {gpu_name}")
    print(f"📹 Input: {actual_resolution} → Output: {resolution_category}")
    print(f"🎯 Codec: {preset_config['codec']} | Preset: {preset_config.get('preset', 'N/A')} | CRF: {settings['crf']}")
    print(f"📦 Container: MKV | Audio: {preset_config['audio_codec']}")
    print(f"⚡ Max Bitrate: {settings['max_bitrate']} | Buffer: {settings['buffer']}")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            universal_newlines=True,
            bufsize=1
        )

        duration = None
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
        duration_pattern = re.compile(r"Duration: (\d+):(\d+):(\d+\.\d+)")

        # Read from stdout since we redirected stderr to stdout
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                    
                # Parse duration from ffmpeg output
                if not duration:
                    match = duration_pattern.search(line)
                    if match:
                        h, m, s = map(float, match.groups())
                        duration = h * 3600 + m * 60 + s

                # Parse current time and calculate progress
                match = time_pattern.search(line)
                if match and duration and duration > 0:
                    h, m, s = map(float, match.groups())
                    current = h * 3600 + m * 60 + s
                    percent = min(round((current / duration) * 100, 2), 100)
                    if progress_callback:
                        progress_callback(percent)

        process.wait()
        
        # Check if the output file was created successfully
        if process.returncode == 0 and os.path.exists(output_path):
            if progress_callback:
                progress_callback(100)  # Ensure we reach 100%
            
            # Clean up original file if encoding was successful
            try:
                if input_path != output_path:  # Don't delete if same file
                    print(f"🗑️ Cleaning up original file: {input_path}")
                    os.remove(input_path)
            except Exception as e:
                print(f"⚠️ Could not remove original file: {e}")
        
        return process.returncode
        
    except FileNotFoundError:
        raise FileNotFoundError("ffmpeg not found. Please ensure ffmpeg with NVENC support is installed.")
    except Exception as e:
        raise RuntimeError(f"NVENC encoding failed: {str(e)}")
