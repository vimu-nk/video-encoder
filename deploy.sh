#!/bin/bash
# Deployment script for Video Encoder Platform on Ubuntu
# Run this script as root or with sudo

set -e  # Exit on any error

echo "🚀 Deploying Video Encoder Platform on Ubuntu..."

# Configuration
APP_USER="video-encoder"
APP_DIR="/opt/video-encoder"
APP_REPO="https://github.com/your-username/video-encoder.git"  # Update this URL
SERVICE_NAME="video-encoder"
DOMAIN="your-domain.com"  # Update this

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run this script as root or with sudo"
    exit 1
fi

# Update system
log "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
log "Installing required packages..."
apt install -y python3 python3-pip python3-venv git nginx ffmpeg certbot python3-certbot-nginx htop

# Create application user
log "Creating application user: $APP_USER"
if ! id "$APP_USER" &>/dev/null; then
    adduser --system --group --home "$APP_DIR" "$APP_USER"
    mkdir -p "$APP_DIR"
    chown "$APP_USER:$APP_USER" "$APP_DIR"
else
    log "User $APP_USER already exists"
fi

# Clone or update repository
log "Setting up application code..."
if [ -d "$APP_DIR/app" ]; then
    log "Updating existing repository..."
    cd "$APP_DIR/app"
    sudo -u "$APP_USER" git pull
else
    log "Cloning repository..."
    sudo -u "$APP_USER" git clone "$APP_REPO" "$APP_DIR/app"
fi

cd "$APP_DIR/app"

# Set up Python virtual environment
log "Setting up Python virtual environment..."
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
fi

sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r requirements.txt

# Create directories
log "Creating application directories..."
sudo -u "$APP_USER" mkdir -p "$APP_DIR/app/logs"
sudo -u "$APP_USER" mkdir -p "$APP_DIR/app/input"
sudo -u "$APP_USER" mkdir -p "$APP_DIR/app/output"

# Set up environment file
log "Setting up environment configuration..."
if [ ! -f "$APP_DIR/app/.env" ]; then
    sudo -u "$APP_USER" cp "$APP_DIR/app/.env.example" "$APP_DIR/app/.env"
    warn "Please edit $APP_DIR/app/.env with your Bunny CDN credentials"
    warn "nano $APP_DIR/app/.env"
fi

# Install systemd service
log "Installing systemd service..."
cp "$APP_DIR/app/video-encoder.service" "/etc/systemd/system/"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# Set up Nginx
log "Setting up Nginx configuration..."
cp "$APP_DIR/app/nginx-video-encoder" "/etc/nginx/sites-available/video-encoder"

# Update domain in Nginx config
sed -i "s/your-domain.com/$DOMAIN/g" "/etc/nginx/sites-available/video-encoder"

# Enable Nginx site
ln -sf "/etc/nginx/sites-available/video-encoder" "/etc/nginx/sites-enabled/"
nginx -t
systemctl reload nginx

# Set up firewall
log "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# Test application
log "Testing application..."
if sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" -c "import app.main; print('✓ Application imports successfully')"; then
    log "Application test passed"
else
    error "Application test failed"
    exit 1
fi

# Start services
log "Starting services..."
systemctl start "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager

# Create management scripts
log "Creating management scripts..."
cat > "$APP_DIR/manage.sh" << 'EOF'
#!/bin/bash
# Management script for Video Encoder Platform

case "$1" in
    start)
        sudo systemctl start video-encoder
        ;;
    stop)
        sudo systemctl stop video-encoder
        ;;
    restart)
        sudo systemctl restart video-encoder
        ;;
    status)
        sudo systemctl status video-encoder
        ;;
    logs)
        sudo journalctl -u video-encoder -f
        ;;
    update)
        cd /opt/video-encoder/app
        sudo -u video-encoder git pull
        sudo -u video-encoder /opt/video-encoder/venv/bin/pip install -r requirements.txt
        sudo systemctl restart video-encoder
        ;;
    ssl)
        sudo certbot --nginx -d $2
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update|ssl domain.com}"
        exit 1
        ;;
esac
EOF

chmod +x "$APP_DIR/manage.sh"
ln -sf "$APP_DIR/manage.sh" "/usr/local/bin/video-encoder-manage"

# Final instructions
log "✅ Deployment completed!"
echo ""
echo "🎉 Video Encoder Platform has been deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit environment file: nano $APP_DIR/app/.env"
echo "2. Add your Bunny CDN credentials"
echo "3. Restart the service: systemctl restart video-encoder"
echo "4. Test the application: curl http://localhost:8000"
echo "5. Set up SSL: certbot --nginx -d $DOMAIN"
echo ""
echo "🔧 Management commands:"
echo "  video-encoder-manage start|stop|restart|status|logs|update"
echo "  video-encoder-manage ssl your-domain.com"
echo ""
echo "🌐 Access your application:"
echo "  HTTP:  http://$DOMAIN"
echo "  HTTPS: https://$DOMAIN (after SSL setup)"
echo ""
echo "📊 Monitor logs:"
echo "  sudo journalctl -u video-encoder -f"
echo ""
warn "Don't forget to configure your domain's DNS to point to this server!"

exit 0
