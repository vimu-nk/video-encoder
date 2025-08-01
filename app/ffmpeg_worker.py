import subprocess
import os
import logging
import threading
import time
import json
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

class FFmpegWorker:
    def __init__(self):
        self.current_process = None
        self.current_thread = None
        self.is_running = False
        self.progress_callback = None
        
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], 
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4:
                        gpus.append({
                            'name': parts[0],
                            'memory_total': f"{parts[1]} MB",
                            'memory_used': f"{parts[2]} MB", 
                            'utilization': f"{parts[3]}%"
                        })
                return {'available': True, 'gpus': gpus}
        except Exception as e:
            logger.warning(f"nvidia-smi not available: {e}")
        
        return {'available': False, 'gpus': []}

    def get_nvenc_capabilities(self) -> Dict[str, bool]:
        """Check which NVENC encoders are available"""
        capabilities = {
            'hevc': False, 
            'h264': False
        }
        
        try:
            # Check for NVENC encoders using ffmpeg
            result = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], 
                                    capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Check for specific NVENC encoders (AV1 removed)
                if 'hevc_nvenc' in output:
                    capabilities['hevc'] = True
                if 'h264_nvenc' in output:
                    capabilities['h264'] = True
                    
        except Exception as e:
            logger.error(f"Error checking NVENC capabilities: {e}")
            
        return capabilities

    def get_video_resolution(self, input_file: str) -> Tuple[int, int]:
        """Get video resolution (width, height)"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    width = int(parts[0])
                    height = int(parts[1])
                    return width, height
        except Exception as e:
            logger.error(f"Error getting video resolution: {e}")
        
        return 1920, 1080  # Default to 1080p if detection fails

    def get_optimized_settings(self, width: int, height: int) -> Dict[str, Any]:
        """Get optimized VBR settings based on resolution for 120MB/10min target"""
        # Calculate total pixels
        pixels = width * height
        
        # Target: 120MB for 10 minutes = 12MB/min = 1.6Mbps average
        # VBR settings optimized by resolution (scaled from 1080p: 1000k avg, 1500k max)
        if pixels <= 640 * 360:  # 360p and below
            return {
                'avg_bitrate': '300k',
                'max_bitrate': '450k', 
                'crf': 30,
                'preset': 'medium'
            }
        elif pixels <= 720 * 480:  # SD (480p)
            return {
                'avg_bitrate': '450k',
                'max_bitrate': '650k', 
                'crf': 28,
                'preset': 'medium'
            }
        elif pixels <= 1280 * 720:  # HD (720p)
            return {
                'avg_bitrate': '700k',
                'max_bitrate': '1000k',
                'crf': 26,
                'preset': 'medium'
            }
        elif pixels <= 1920 * 1080:  # Full HD (1080p)
            return {
                'avg_bitrate': '1000k',
                'max_bitrate': '1500k',
                'crf': 24,
                'preset': 'medium'
            }
        elif pixels <= 2560 * 1440:  # QHD (1440p)
            return {
                'avg_bitrate': '1600k',
                'max_bitrate': '2400k',
                'crf': 22,
                'preset': 'slow'
            }
        else:  # 4K and above
            return {
                'avg_bitrate': '2500k',
                'max_bitrate': '3500k',
                'crf': 20,
                'preset': 'slow'
            }

    def get_ffmpeg_preset(self, codec: str, input_file: str, has_nvenc: bool) -> Dict[str, Any]:
        """Get FFmpeg encoding preset based on codec and video resolution (VBR optimized for 120MB/10min)"""
        
        # Base audio settings - AAC stereo
        audio_settings = ['-c:a', 'aac', '-b:a', '128k', '-ac', '2']
        
        # Get video resolution for optimization
        width, height = self.get_video_resolution(input_file)
        settings = self.get_optimized_settings(width, height)
        
        # Remove AV1, focus on HEVC and H.264 with VBR
        if codec == 'hevc_nvenc' and has_nvenc:
            return {
                'video_codec': ['-c:v', 'hevc_nvenc'],
                'quality': [
                    '-b:v', settings['avg_bitrate'],
                    '-maxrate', settings['max_bitrate'], 
                    '-bufsize', str(int(settings['max_bitrate'].replace('k', '')) * 2) + 'k',
                    '-cq', str(settings['crf']),
                    '-preset', settings['preset']
                ],
                'audio': audio_settings,
                'output_format': 'mp4'
            }
        elif codec == 'h264_nvenc' and has_nvenc:
            return {
                'video_codec': ['-c:v', 'h264_nvenc'],
                'quality': [
                    '-b:v', settings['avg_bitrate'],
                    '-maxrate', settings['max_bitrate'],
                    '-bufsize', str(int(settings['max_bitrate'].replace('k', '')) * 2) + 'k',
                    '-cq', str(settings['crf']),
                    '-preset', settings['preset']
                ],
                'audio': audio_settings,
                'output_format': 'mp4'
            }
        else:
            # Fallback to CPU encoding with x265 VBR
            return {
                'video_codec': ['-c:v', 'libx265'],
                'quality': [
                    '-b:v', settings['avg_bitrate'],
                    '-maxrate', settings['max_bitrate'],
                    '-bufsize', str(int(settings['max_bitrate'].replace('k', '')) * 2) + 'k',
                    '-crf', str(settings['crf']),
                    '-preset', settings['preset']
                ],
                'audio': audio_settings,
                'output_format': 'mp4'
            }

    def build_ffmpeg_command(self, input_file: str, output_file: str, preset: Dict[str, Any]) -> List[str]:
        """Build complete FFmpeg command"""
        cmd = ['ffmpeg', '-i', input_file]
        
        # Add video codec
        cmd.extend(preset['video_codec'])
        
        # Add quality settings
        cmd.extend(preset['quality'])
        
        # Add audio settings
        cmd.extend(preset['audio'])
        
        # Add output file
        cmd.append(output_file)
        
        return cmd

    def parse_ffmpeg_progress(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse FFmpeg progress from output line"""
        if 'frame=' in line and 'fps=' in line and 'time=' in line:
            try:
                parts = line.split()
                progress = {}
                
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        if key in ['frame', 'fps', 'q', 'size', 'time', 'bitrate', 'speed']:
                            progress[key] = value
                
                return progress
            except Exception:
                pass
        return None

    def get_video_duration(self, input_file: str) -> Optional[float]:
        """Get video duration in seconds"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                return duration
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
        
        return None

    def time_to_seconds(self, time_str: str) -> Optional[float]:
        """Convert time string (HH:MM:SS.ms) to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1]) 
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except Exception:
            pass
        return None

    def calculate_progress_percentage(self, current_time: str, total_duration: float) -> Optional[float]:
        """Calculate encoding progress percentage"""
        current_seconds = self.time_to_seconds(current_time)
        if current_seconds and total_duration:
            percentage = (current_seconds / total_duration) * 100
            return min(percentage, 100.0)
        return None

    def run_ffmpeg(self, input_file: str, output_file: str, codec: str, 
                   progress_callback=None) -> Tuple[bool, str]:
        """Run FFmpeg encoding with VBR and resolution-based optimization"""
        
        try:
            # Check NVENC capabilities
            nvenc_caps = self.get_nvenc_capabilities()
            has_nvenc = any(nvenc_caps.values())
            
            # Get encoding preset (now uses input file for resolution detection)
            preset = self.get_ffmpeg_preset(codec, input_file, has_nvenc)
            
            # Build command
            cmd = self.build_ffmpeg_command(input_file, output_file, preset)
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Get video duration for progress calculation
            total_duration = self.get_video_duration(input_file)
            
            # Start FFmpeg process
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.is_running = True
            
            # Monitor progress
            while True:
                if self.current_process.stdout is None:
                    break
                output = self.current_process.stdout.readline()
                if output == '' and self.current_process.poll() is not None:
                    break
                
                if output:
                    # Parse progress
                    progress_data = self.parse_ffmpeg_progress(output.strip())
                    
                    if progress_data and progress_callback:
                        # Calculate percentage if we have duration
                        if total_duration and 'time' in progress_data:
                            percentage = self.calculate_progress_percentage(
                                progress_data['time'], total_duration
                            )
                            if percentage:
                                progress_data['percentage'] = round(percentage, 1)
                        
                        progress_callback(progress_data)
            
            # Get final return code
            return_code = self.current_process.poll()
            self.is_running = False
            
            if return_code == 0:
                return True, "Encoding completed successfully"
            else:
                return False, f"FFmpeg failed with return code {return_code}"
                
        except Exception as e:
            self.is_running = False
            logger.error(f"Error running FFmpeg: {e}")
            return False, f"Error: {str(e)}"

    def stop_encoding(self):
        """Stop current encoding process"""
        if self.current_process and self.is_running:
            try:
                self.current_process.terminate()
                # Wait a bit for graceful termination
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    self.current_process.kill()
                    self.current_process.wait()
                
                self.is_running = False
                return True, "Encoding stopped"
            except Exception as e:
                logger.error(f"Error stopping encoding: {e}")
                return False, f"Error stopping: {str(e)}"
        
        return False, "No encoding process running"

    def get_encoding_status(self) -> Dict[str, Any]:
        """Get current encoding status"""
        return {
            'is_running': self.is_running,
            'has_process': self.current_process is not None
        }

    def get_supported_codecs(self) -> List[Dict[str, str]]:
        """Get list of supported codecs with their display names"""
        nvenc_caps = self.get_nvenc_capabilities()
        has_nvenc = any(nvenc_caps.values())
        
        codecs = []
        
        if has_nvenc:
            if nvenc_caps['hevc']:
                codecs.append({'value': 'hevc_nvenc', 'name': 'HEVC (NVENC) - Best Quality'})
            if nvenc_caps['h264']:
                codecs.append({'value': 'h264_nvenc', 'name': 'H.264 (NVENC) - Universal'})
        
        # Always include CPU fallback
        codecs.append({'value': 'x265', 'name': 'HEVC (x265 CPU) - Fallback'})
        
        return codecs

    def validate_input_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate input video file"""
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "File is empty"
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
        except Exception as e:
            return False, f"File is not readable: {str(e)}"
        
        # Basic video file extension check
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in valid_extensions:
            return False, f"Unsupported file extension: {file_ext}"
        
        return True, "File is valid"

    def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed video file information"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract video stream info
                video_stream = None
                audio_streams = []
                
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio':
                        audio_streams.append(stream)
                
                info = {
                    'format': data.get('format', {}),
                    'video_stream': video_stream,
                    'audio_streams': audio_streams,
                    'duration': float(data['format']['duration']) if 'format' in data and 'duration' in data['format'] else None
                }
                
                return info
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
        
        return {}

# Global instance
ffmpeg_worker = FFmpegWorker()

def get_gpu_info():
    """Get GPU information"""
    return ffmpeg_worker.get_gpu_info()

def get_nvenc_capabilities():
    """Get NVENC capabilities"""
    return ffmpeg_worker.get_nvenc_capabilities()

def get_supported_codecs():
    """Get supported codecs"""
    return ffmpeg_worker.get_supported_codecs()

def run_encoding(input_file: str, output_file: str, codec: str, progress_callback=None):
    """Run encoding with progress tracking (VBR optimized)"""
    return ffmpeg_worker.run_ffmpeg(input_file, output_file, codec, progress_callback)

def stop_encoding():
    """Stop current encoding"""
    return ffmpeg_worker.stop_encoding()

def get_encoding_status():
    """Get encoding status"""
    return ffmpeg_worker.get_encoding_status()

def validate_input_file(file_path: str):
    """Validate input file"""
    return ffmpeg_worker.validate_input_file(file_path)

def get_video_info(file_path: str):
    """Get video file information"""
    return ffmpeg_worker.get_video_info(file_path)
