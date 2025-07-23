#!/bin/bash
# Update script for Video Encoder Platform

set -e

APP_USER="video-encoder"
APP_DIR="/opt/video-encoder/app"
SERVICE_NAME="video-encoder"

echo "🔄 Updating Video Encoder Platform..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script as root or with sudo"
    exit 1
fi

# Navigate to app directory
cd "$APP_DIR"

# Backup current version
echo "📦 Creating backup..."
sudo -u "$APP_USER" cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Pull latest changes
echo "📥 Pulling latest changes..."
sudo -u "$APP_USER" git pull

# Update dependencies
echo "📦 Updating dependencies..."
sudo -u "$APP_USER" /opt/video-encoder/venv/bin/pip install -r requirements.txt

# Run any database migrations (if applicable in future)
echo "🔄 Running migrations..."
# sudo -u "$APP_USER" /opt/video-encoder/venv/bin/python manage.py migrate

# Restart service
echo "🔄 Restarting service..."
systemctl restart "$SERVICE_NAME"

# Wait a moment and check status
sleep 5
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Update completed successfully!"
    echo "🌐 Service is running at: http://$(hostname -I | awk '{print $1}'):8000"
else
    echo "❌ Service failed to start after update"
    echo "📋 Check logs: journalctl -u $SERVICE_NAME -f"
    exit 1
fi
