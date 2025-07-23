import subprocess

def encode_to_hevc(input_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx265", "-pix_fmt", "yuv420p10le",
        "-crf", "24", "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result
