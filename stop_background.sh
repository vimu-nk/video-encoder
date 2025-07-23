#!/bin/bash
# Stop the background Video Encoder Platform

if pgrep -f "service.py" > /dev/null; then
    echo "Stopping Video Encoder Platform..."
    pkill -f "service.py"
    
    # Wait a moment
    sleep 2
    
    if pgrep -f "service.py" > /dev/null; then
        echo "Force killing..."
        pkill -9 -f "service.py"
    fi
    
    # Clean up PID file
    rm -f logs/service.pid
    
    echo "✅ Video Encoder Platform stopped"
else
    echo "Video Encoder Platform is not running"
fi
