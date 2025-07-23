import subprocess
import re
import os

def run_ffmpeg(input_path, output_path, progress_callback=None):
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    command = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx265",
        "-preset", "slow",
        "-crf", "28",
        "-pix_fmt", "yuv420p10le",
        "-c:a", "copy",
        "-y",  # Overwrite output file
        output_path
    ]

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
