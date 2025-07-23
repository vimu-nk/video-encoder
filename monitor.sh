#!/bin/bash
# Monitoring and alerting script for Video Encoder Platform
# Add to crontab: */5 * * * * /opt/video-encoder/app/monitor.sh

# Configuration
ALERT_EMAIL="admin@yourdomain.com"  # Update with your email
WEBHOOK_URL=""  # Optional: Slack/Discord webhook URL
SERVICE_NAME="video-encoder"
APP_DIR="/opt/video-encoder/app"
STATUS_FILE="/tmp/video-encoder-status"

# Load previous status
if [ -f "$STATUS_FILE" ]; then
    PREV_STATUS=$(cat "$STATUS_FILE")
else
    PREV_STATUS="unknown"
fi

# Run health check
if "$APP_DIR/health_check.sh" >/dev/null 2>&1; then
    CURRENT_STATUS="healthy"
else
    CURRENT_STATUS="unhealthy"
fi

# Save current status
echo "$CURRENT_STATUS" > "$STATUS_FILE"

# Alert if status changed from healthy to unhealthy
if [ "$PREV_STATUS" = "healthy" ] && [ "$CURRENT_STATUS" = "unhealthy" ]; then
    ALERT_MSG="🚨 Video Encoder Platform is DOWN on $(hostname)"
    
    # Send email alert (if mail is configured)
    if command -v mail >/dev/null 2>&1; then
        echo "$ALERT_MSG" | mail -s "Video Encoder Alert" "$ALERT_EMAIL"
    fi
    
    # Send webhook alert (if configured)
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
             --data '{"text":"'"$ALERT_MSG"'"}' \
             "$WEBHOOK_URL"
    fi
    
    # Log to syslog
    logger -t video-encoder "$ALERT_MSG"
fi

# Alert if status changed from unhealthy to healthy
if [ "$PREV_STATUS" = "unhealthy" ] && [ "$CURRENT_STATUS" = "healthy" ]; then
    RECOVERY_MSG="✅ Video Encoder Platform is UP on $(hostname)"
    
    # Send email alert (if mail is configured)
    if command -v mail >/dev/null 2>&1; then
        echo "$RECOVERY_MSG" | mail -s "Video Encoder Recovery" "$ALERT_EMAIL"
    fi
    
    # Send webhook alert (if configured)
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
             --data '{"text":"'"$RECOVERY_MSG"'"}' \
             "$WEBHOOK_URL"
    fi
    
    # Log to syslog
    logger -t video-encoder "$RECOVERY_MSG"
fi

exit 0
