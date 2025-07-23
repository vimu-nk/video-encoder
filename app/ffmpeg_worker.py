import subprocess
import re

def run_ffmpeg(input_path, output_path, progress_callback=None):
    command = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx265",
        "-preset", "slow",
        "-crf", "28",
        "-pix_fmt", "yuv420p10le",
        "-c:a", "copy",
        output_path,
        "-y"
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    duration = None
    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
    duration_pattern = re.compile(r"Duration: (\d+):(\d+):(\d+\.\d+)")

    for line in process.stderr:
        if not duration:
            match = duration_pattern.search(line)
            if match:
                h, m, s = map(float, match.groups())
                duration = h * 3600 + m * 60 + s

        match = time_pattern.search(line)
        if match and duration:
            h, m, s = map(float, match.groups())
            current = h * 3600 + m * 60 + s
            percent = round((current / duration) * 100, 2)
            if progress_callback:
                progress_callback(percent)

    process.wait()
    return process.returncode
