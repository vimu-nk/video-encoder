#!/bin/bash

# Video Encoder Platform - Background Startup Script
# This script starts the FastAPI application in the background and manages it

set -e

# Configuration
APP_DIR="$(pwd)"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/video-encoder.pid"
LOG_FILE="$LOG_DIR/application.log"
ACCESS_LOG="$LOG_DIR/access.log"
ERROR_LOG="$LOG_DIR/error.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function to check if service is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to get service status
get_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        print_success "Video Encoder is running (PID: $PID)"
        
        # Check if the service is responding
        if curl -s -f http://localhost:8000/api/status >/dev/null 2>&1; then
            print_success "Service is responding to HTTP requests"
        else
            print_warning "Service is running but not responding to HTTP requests"
        fi
        
        # Show resource usage
        if command -v ps >/dev/null 2>&1; then
            CPU_MEM=$(ps -p "$PID" -o pid,pcpu,pmem,etime --no-headers 2>/dev/null || true)
            if [ -n "$CPU_MEM" ]; then
                print_status "Resource usage: $CPU_MEM"
            fi
        fi
        
        return 0
    else
        print_error "Video Encoder is not running"
        return 1
    fi
}

# Function to start the service
start_service() {
    print_status "Starting Video Encoder service..."
    
    if is_running; then
        print_warning "Service is already running"
        get_status
        return 0
    fi
    
    # Create necessary directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$APP_DIR/input"
    mkdir -p "$APP_DIR/output"
    
    # Change to app directory
    cd "$APP_DIR"
    
    # Check dependencies
    print_status "Checking dependencies..."
    if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        print_error "Missing required Python packages. Installing..."
        pip3 install -r requirements.txt
    fi
    
    # Verify app module can be imported
    print_status "Verifying app module..."
    if ! python3 -c "import sys; sys.path.insert(0, '.'); from app.main import app" 2>/dev/null; then
        print_error "Cannot import app module. Checking structure..."
        ls -la app/
        print_error "Make sure you're running from the correct directory with app/ subdirectory"
        exit 1
    fi
    
    # Check for GPU and NVENC
    print_status "Checking hardware capabilities..."
    if command -v nvidia-smi >/dev/null 2>&1; then
        print_success "NVIDIA GPU detected:"
        nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits | head -1
    else
        print_warning "nvidia-smi not available, checking NVENC via ffmpeg..."
    fi
    
    if command -v ffmpeg >/dev/null 2>&1; then
        NVENC_COUNT=$(ffmpeg -hide_banner -encoders 2>/dev/null | grep nvenc | wc -l)
        if [ "$NVENC_COUNT" -gt 0 ]; then
            print_success "NVENC encoders available: $NVENC_COUNT"
            ffmpeg -hide_banner -encoders 2>/dev/null | grep nvenc | head -3
        else
            print_warning "No NVENC encoders detected - will use CPU encoding"
        fi
    else
        print_error "FFmpeg not found!"
        exit 1
    fi
    
    # Start the service in background
    print_status "Starting FastAPI application..."
    print_status "Working directory: $(pwd)"
    print_status "Python path: $PYTHONPATH"
    
    # Set PYTHONPATH to include current directory so 'app' module can be found
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"
    
    # Create a startup script to ensure proper environment
    cat > "$LOG_DIR/start_uvicorn.sh" << EOF
#!/bin/bash
cd "$APP_DIR"
export PYTHONPATH="$APP_DIR:\$PYTHONPATH"
exec python3 -m uvicorn app.main:app \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --workers 1 \\
    --access-log \\
    --log-level info
EOF
    
    chmod +x "$LOG_DIR/start_uvicorn.sh"
    
    nohup "$LOG_DIR/start_uvicorn.sh" > "$LOG_FILE" 2>&1 &
    
    PID=$!
    echo "$PID" > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    
    if is_running; then
        print_success "Video Encoder started successfully (PID: $PID)"
        print_status "Application logs: $LOG_FILE"
        print_status "Service available at: http://localhost:8000"
        
        # Wait for service to be ready
        print_status "Waiting for service to be ready..."
        for i in {1..30}; do
            if curl -s -f http://localhost:8000/api/status >/dev/null 2>&1; then
                print_success "Service is ready and responding!"
                break
            fi
            sleep 1
            echo -n "."
        done
        echo
        
        return 0
    else
        print_error "Failed to start Video Encoder"
        if [ -f "$LOG_FILE" ]; then
            print_error "Last 10 lines of log:"
            tail -10 "$LOG_FILE"
        fi
        return 1
    fi
}

# Function to stop the service
stop_service() {
    print_status "Stopping Video Encoder service..."
    
    if ! is_running; then
        print_warning "Service is not running"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    # Try graceful shutdown first
    print_status "Sending TERM signal to PID $PID..."
    kill -TERM "$PID" 2>/dev/null || true
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        print_warning "Graceful shutdown failed, forcing termination..."
        kill -KILL "$PID" 2>/dev/null || true
        sleep 2
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    if ! kill -0 "$PID" 2>/dev/null; then
        print_success "Video Encoder stopped successfully"
        return 0
    else
        print_error "Failed to stop Video Encoder"
        return 1
    fi
}

# Function to restart the service
restart_service() {
    print_status "Restarting Video Encoder service..."
    stop_service
    sleep 2
    start_service
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
            print_status "Following application logs (Ctrl+C to exit):"
            tail -f "$LOG_FILE"
        else
            print_status "Showing last 50 lines of application logs:"
            tail -50 "$LOG_FILE"
        fi
    else
        print_error "Log file not found: $LOG_FILE"
        return 1
    fi
}

# Function to show service information
show_info() {
    print_status "=== Video Encoder Service Information ==="
    echo
    print_status "Configuration:"
    echo "  App Directory: $APP_DIR"
    echo "  Log Directory: $LOG_DIR"
    echo "  PID File: $PID_FILE"
    echo "  Service URL: http://localhost:8000"
    echo
    
    print_status "File Status:"
    [ -d "$APP_DIR" ] && echo "  ✓ App directory exists" || echo "  ✗ App directory missing"
    [ -f "$APP_DIR/requirements.txt" ] && echo "  ✓ Requirements file found" || echo "  ✗ Requirements file missing"
    [ -f "$APP_DIR/app/main.py" ] && echo "  ✓ Main application found" || echo "  ✗ Main application missing"
    echo
    
    get_status
}

# Function to show usage
show_usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|info|help}"
    echo
    echo "Commands:"
    echo "  start    - Start the Video Encoder service"
    echo "  stop     - Stop the Video Encoder service"  
    echo "  restart  - Restart the Video Encoder service"
    echo "  status   - Show service status"
    echo "  logs     - Show application logs (use -f to follow)"
    echo "  info     - Show service information"
    echo "  help     - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs -f"
    echo "  $0 restart"
}

# Main script logic
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        get_status
        ;;
    logs)
        show_logs "$2"
        ;;
    info)
        show_info
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Invalid command: $1"
        echo
        show_usage
        exit 1
        ;;
esac

exit $?
