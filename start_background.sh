#!/bin/bash
# Simple background runner for Video Encoder Platform
# For personal use on Ubuntu server

cd "$(dirname "$0")"

# Check if already running
if pgrep -f "service.py" > /dev/null; then
    echo "Video Encoder Platform is already running"
    echo "PID: $(pgrep -f service.py)"
    echo "Access at: http://$(hostname -I | awk '{print $1}'):8000"
    exit 0
fi

# Create logs directory
mkdir -p logs

# Start in background with nohup
echo "Starting Video Encoder Platform in background..."
nohup python3 service.py > logs/service.log 2>&1 &

# Get the PID
PID=$!
echo $PID > logs/service.pid

echo "✅ Video Encoder Platform started successfully!"
echo "PID: $PID"
echo "Logs: logs/service.log"
echo "Access at: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "To stop: kill $PID"
echo "Or use: pkill -f service.py"
