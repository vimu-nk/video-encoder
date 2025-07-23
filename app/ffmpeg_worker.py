import subprocess
import re
import os
import multiprocessing

def get_cpu_info():
    """Get CPU information for optimal threading"""
    try:
        cpu_count = multiprocessing.cpu_count()
        # For x265, optimal thread count is usually CPU cores * 1.5 to 2
        optimal_threads = min(cpu_count * 2, 32)  # Cap at 32 threads
        return {
            "cpu_count": cpu_count,
            "optimal_threads": optimal_threads,
            "pool_threads": max(1, cpu_count // 2)  # For frame pools
        }
    except:
        return {
            "cpu_count": 4,
            "optimal_threads": 8,
            "pool_threads": 2
        }

def get_resolution_bitrates():
    """Get bitrate settings based on resolution"""
    return {
        "1080p": "1500k",  # 1.5 MB/s for 1080p
        "720p": "1000k",   # 1 MB/s for 720p  
        "480p": "750k",    # 750 KB/s for 480p
        "360p": "500k"     # 500 KB/s for 360p
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
                
                # Determine resolution category based on height
                if height >= 1080:
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
    """Get FFmpeg settings based on preset name - all using x265 with resolution-based bitrates"""
    presets = {
        "ultrafast": {
            "codec": "libx265",
            "preset": "ultrafast", 
            "pix_fmt": "yuv420p",
            "extra_args": ["-tune", "fastdecode"]
        },
        "superfast": {
            "codec": "libx265",
            "preset": "superfast",
            "pix_fmt": "yuv420p",
            "extra_args": []
        },
        "veryfast": {
            "codec": "libx265",
            "preset": "veryfast",
            "pix_fmt": "yuv420p",
            "extra_args": []
        },
        "fast": {
            "codec": "libx265",
            "preset": "fast",
            "pix_fmt": "yuv420p",
            "extra_args": []
        },
        "medium": {
            "codec": "libx265",
            "preset": "medium",
            "pix_fmt": "yuv420p",
            "extra_args": []
        },
        "slow_hq": {
            "codec": "libx265",
            "preset": "slow",
            "pix_fmt": "yuv420p10le",
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
    
    # Get CPU information for optimal threading
    cpu_info = get_cpu_info()
    
    # Detect video resolution and get appropriate bitrate
    resolution_category, actual_resolution = detect_resolution(input_path)
    bitrates = get_resolution_bitrates()
    target_bitrate = bitrates[resolution_category]
    
    # Get preset settings
    preset_config = get_ffmpeg_preset(preset_name)
    
    if progress_callback:
        progress_callback(5)  # Initial progress
    
    # Build command with x265 and maximum CPU utilization
    command = [
        "ffmpeg",
        
        # Hardware acceleration (try to use if available) - MUST be before input
        "-hwaccel", "auto",
        "-hwaccel_output_format", "auto",
        
        "-i", input_path,
        
        # Video encoding settings
        "-c:v", preset_config["codec"],
        "-preset", preset_config["preset"],
        "-b:v", target_bitrate,
        "-maxrate", target_bitrate,
        "-bufsize", f"{int(target_bitrate.rstrip('k')) * 2}k",
        "-pix_fmt", preset_config["pix_fmt"],
        
        # Audio settings
        "-c:a", "aac",
        "-b:a", "128k",
        
        # Enhanced multi-threading configuration
        "-threads", str(cpu_info["optimal_threads"]),
        "-thread_type", "frame+slice",
        "-slices", str(cpu_info["cpu_count"]),
        "-filter_complex_threads", str(cpu_info["cpu_count"]),
        
        # Streaming and performance optimizations
        "-movflags", "+faststart",
        "-avoid_negative_ts", "make_zero",
        "-fflags", "+genpts",
    ]
    
    # Add x265-specific optimizations (with error handling)
    if preset_config["codec"] == "libx265":
        x265_params = f"pools={cpu_info['pool_threads']}:frame-threads={cpu_info['cpu_count']}:wpp:pmode:pme:asm=avx2"
        command.extend(["-x265-params", x265_params])
    
    # Add extra arguments if any
    command.extend(preset_config["extra_args"])
    
    # Add output file and overwrite flag
    command.extend(["-y", output_path])
    
    print(f"Encoding {actual_resolution} video with {target_bitrate} bitrate using {preset_config['codec']} {preset_config['preset']} preset")
    print(f"CPU Utilization: {cpu_info['cpu_count']} cores, {cpu_info['optimal_threads']} threads, {cpu_info['pool_threads']} pools")

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
        
        return process.returncode
        
    except FileNotFoundError:
        raise FileNotFoundError("ffmpeg not found. Please ensure ffmpeg is installed and in your PATH.")
    except Exception as e:
        raise RuntimeError(f"FFmpeg encoding failed: {str(e)}")
