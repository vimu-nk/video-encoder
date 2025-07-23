#!/usr/bin/env python3
"""
Cross-platform daemon/background service starter
"""
import os
import sys
import subprocess
import platform
import signal
import time
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent.absolute()
        self.pid_file = self.script_dir / "logs" / "service.pid"
        self.log_file = self.script_dir / "logs" / "service.log"
        
        # Ensure logs directory exists
        self.pid_file.parent.mkdir(exist_ok=True)
    
    def is_running(self):
        """Check if service is already running"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            if self.platform == "windows":
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                      capture_output=True, text=True)
                return str(pid) in result.stdout
            else:
                try:
                    os.kill(pid, 0)  # Send signal 0 to check if process exists
                    return True
                except OSError:
                    return False
        except (ValueError, FileNotFoundError):
            return False
    
    def start_windows(self):
        """Start service on Windows"""
        print("Starting Video Encoder Platform on Windows...")
        
        # Use pythonw.exe to run without console window
        python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
        if not os.path.exists(python_exe):
            python_exe = sys.executable
        
        # Start process in background
        process = subprocess.Popen(
            [python_exe, str(self.script_dir / "service.py")],
            cwd=str(self.script_dir),
            stdout=open(self.log_file, 'a'),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        
        # Save PID
        with open(self.pid_file, 'w') as f:
            f.write(str(process.pid))
        
        print(f"✓ Service started with PID: {process.pid}")
        return process.pid
    
    def start_unix(self):
        """Start service on Unix-like systems"""
        print("Starting Video Encoder Platform as daemon...")
        
        # Fork process to run in background
        pid = os.fork()
        if pid == 0:
            # Child process
            os.setsid()  # Create new session
            
            # Second fork to ensure daemon
            pid2 = os.fork()
            if pid2 == 0:
                # Grandchild process - this becomes the daemon
                os.chdir(str(self.script_dir))
                
                # Redirect stdout/stderr to log file
                with open(self.log_file, 'a') as log:
                    os.dup2(log.fileno(), sys.stdout.fileno())
                    os.dup2(log.fileno(), sys.stderr.fileno())
                
                # Run the service
                subprocess.run([sys.executable, str(self.script_dir / "service.py")])
            else:
                # First child exits
                sys.exit(0)
        else:
            # Parent process
            # Wait for first child to exit
            os.waitpid(pid, 0)
            
            # Give daemon time to start
            time.sleep(2)
            
            # Find the actual daemon PID (grandchild)
            # This is a simplified approach - in production you'd want better PID tracking
            result = subprocess.run(['pgrep', '-f', 'service.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                daemon_pid = result.stdout.strip().split('\n')[0]
                with open(self.pid_file, 'w') as f:
                    f.write(daemon_pid)
                print(f"✓ Service started with PID: {daemon_pid}")
                return int(daemon_pid)
            else:
                print("✗ Failed to start service")
                return None
    
    def start(self):
        """Start the service"""
        if self.is_running():
            print("Service is already running")
            return
        
        if self.platform == "windows":
            return self.start_windows()
        else:
            return self.start_unix()
    
    def stop(self):
        """Stop the service"""
        if not self.is_running():
            print("Service is not running")
            return
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            print(f"Stopping service with PID: {pid}")
            
            if self.platform == "windows":
                subprocess.run(['taskkill', '/PID', str(pid), '/F'], 
                             capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    try:
                        os.kill(pid, 0)
                        time.sleep(1)
                    except OSError:
                        break
                else:
                    # Force kill if still running
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
            
            # Remove PID file
            self.pid_file.unlink(missing_ok=True)
            print("✓ Service stopped")
            
        except (ValueError, FileNotFoundError, ProcessLookupError) as e:
            print(f"Error stopping service: {e}")
            self.pid_file.unlink(missing_ok=True)
    
    def status(self):
        """Show service status"""
        if self.is_running():
            with open(self.pid_file, 'r') as f:
                pid = f.read().strip()
            print(f"✓ Service is running (PID: {pid})")
            print(f"Dashboard: http://localhost:8000")
            print(f"Logs: {self.log_file}")
        else:
            print("✗ Service is not running")

def main():
    if len(sys.argv) < 2:
        print("Usage: python daemon.py [start|stop|restart|status]")
        return
    
    service = ServiceManager()
    command = sys.argv[1].lower()
    
    if command == "start":
        service.start()
    elif command == "stop":
        service.stop()
    elif command == "restart":
        service.stop()
        time.sleep(2)
        service.start()
    elif command == "status":
        service.status()
    else:
        print("Unknown command. Use: start, stop, restart, or status")

if __name__ == "__main__":
    main()
