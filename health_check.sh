#!/bin/bash
# Health check script for Video Encoder Platform
# Use this for monitoring and alerting

set -e

# Configuration
SERVICE_NAME="video-encoder"
APP_URL="http://localhost:8000"
LOG_FILE="/opt/video-encoder/app/logs/health.log"
MAX_LOG_SIZE=10485760  # 10MB

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Rotate log if it's too large
if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt $MAX_LOG_SIZE ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
fi

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_service() {
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "✓ Service $SERVICE_NAME is running"
        return 0
    else
        log "✗ Service $SERVICE_NAME is not running"
        return 1
    fi
}

check_web_response() {
    if curl -f -s -o /dev/null --max-time 10 "$APP_URL/api/status"; then
        log "✓ Web application is responding"
        return 0
    else
        log "✗ Web application is not responding"
        return 1
    fi
}

check_disk_space() {
    local input_dir="/opt/video-encoder/app/input"
    local output_dir="/opt/video-encoder/app/output"
    local threshold=90  # 90% threshold
    
    # Check root filesystem
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt "$threshold" ]; then
        log "⚠ Disk usage is ${usage}% (threshold: ${threshold}%)"
        return 1
    else
        log "✓ Disk usage is ${usage}%"
    fi
    
    # Clean up old temporary files (older than 24 hours)
    if [ -d "$input_dir" ]; then
        find "$input_dir" -type f -mtime +1 -delete 2>/dev/null || true
    fi
    if [ -d "$output_dir" ]; then
        find "$output_dir" -type f -mtime +1 -delete 2>/dev/null || true
    fi
    
    return 0
}

check_memory() {
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100.0}')
    local threshold=90
    
    if [ "$mem_usage" -gt "$threshold" ]; then
        log "⚠ Memory usage is ${mem_usage}% (threshold: ${threshold}%)"
        return 1
    else
        log "✓ Memory usage is ${mem_usage}%"
        return 0
    fi
}

check_ffmpeg() {
    if command -v ffmpeg >/dev/null 2>&1; then
        log "✓ FFmpeg is available"
        return 0
    else
        log "✗ FFmpeg is not available"
        return 1
    fi
}

# Main health check
main() {
    log "=== Health Check Started ==="
    
    local failures=0
    
    check_service || ((failures++))
    check_web_response || ((failures++))
    check_disk_space || ((failures++))
    check_memory || ((failures++))
    check_ffmpeg || ((failures++))
    
    if [ $failures -eq 0 ]; then
        log "✅ All health checks passed"
        exit 0
    else
        log "❌ $failures health check(s) failed"
        
        # Try to restart service if it's not responding
        if ! check_service || ! check_web_response; then
            log "🔄 Attempting to restart service..."
            systemctl restart "$SERVICE_NAME"
            sleep 10
            
            if check_service && check_web_response; then
                log "✅ Service restarted successfully"
                exit 0
            else
                log "❌ Service restart failed"
                exit 1
            fi
        fi
        
        exit 1
    fi
}

# Run health check
main "$@"
