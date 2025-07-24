#!/bin/bash

# 🚀 DigitalOcean GPU Droplet Deployment Script
# NVIDIA RTX 4000 ADA Optimized Video Encoder

set -e

echo "🚀 Setting up NVENC-Optimized Video Encoder on DigitalOcean GPU Droplet"
echo "============================================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install NVIDIA drivers and CUDA
echo "🖥️ Installing NVIDIA drivers and CUDA..."
sudo apt install -y ubuntu-drivers-common
sudo ubuntu-drivers autoinstall

# Install CUDA toolkit
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-2

# Install FFmpeg with NVENC support
echo "🎬 Installing FFmpeg with NVENC support..."
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:savoury1/ffmpeg4 -y
sudo apt update
sudo apt install -y ffmpeg

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/video-encoder
cd /opt/video-encoder

# Create virtual environment
python3 -m venv encoder-env
source encoder-env/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install fastapi uvicorn python-multipart jinja2 requests

# Create directory structure
mkdir -p input output logs
mkdir -p app/templates

# Copy application files (you'll need to upload these)
echo "📋 Application files should be uploaded to /opt/video-encoder/"
echo "   Required files:"
echo "   - app/main.py"
echo "   - app/ffmpeg_worker.py" 
echo "   - app/bunny_client.py"
echo "   - app/templates/"
echo "   - requirements.txt"

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/video-encoder.service > /dev/null <<EOF
[Unit]
Description=NVENC Video Encoder API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/video-encoder
Environment=PATH=/opt/video-encoder/encoder-env/bin
ExecStart=/opt/video-encoder/encoder-env/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration for reverse proxy
echo "🌐 Setting up Nginx reverse proxy..."
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/video-encoder > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10G;
    client_timeout 300s;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/video-encoder /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Setup firewall
echo "🔒 Configuring firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create monitoring script
echo "📊 Creating monitoring script..."
tee /opt/video-encoder/monitor.sh > /dev/null <<EOF
#!/bin/bash
echo "🖥️ GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv

echo ""
echo "🚀 Service Status:"
systemctl status video-encoder --no-pager -l

echo ""
echo "📊 System Resources:"
free -h
df -h /

echo ""
echo "🔗 Access URLs:"
echo "http://\$(curl -s ifconfig.me)/"
echo "http://\$(curl -s ifconfig.me)/logs"
EOF

chmod +x /opt/video-encoder/monitor.sh

# Create test script
echo "🧪 Creating test script..."
tee /opt/video-encoder/test-nvenc.sh > /dev/null <<EOF
#!/bin/bash
echo "🧪 Testing NVENC capabilities..."

echo "1. GPU Detection:"
nvidia-smi --query-gpu=name --format=csv,noheader

echo ""
echo "2. NVENC Support:"
ffmpeg -encoders 2>/dev/null | grep nvenc

echo ""
echo "3. Test Encode:"
ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 -c:v av1_nvenc -preset p1 -t 5 -y test_nvenc.mkv 2>/dev/null
if [ -f test_nvenc.mkv ]; then
    echo "✅ NVENC AV1 encoding successful!"
    ls -lh test_nvenc.mkv
    rm test_nvenc.mkv
else
    echo "❌ NVENC encoding failed"
fi
EOF

chmod +x /opt/video-encoder/test-nvenc.sh

echo ""
echo "🎉 Installation Complete!"
echo "============================================================================"
echo ""
echo "📋 Next Steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. Upload your application files to /opt/video-encoder/"
echo "3. Test NVENC: /opt/video-encoder/test-nvenc.sh"
echo "4. Start service: sudo systemctl enable --now video-encoder"
echo "5. Monitor system: /opt/video-encoder/monitor.sh"
echo ""
echo "🌐 Access your encoder at: http://YOUR_DROPLET_IP/"
echo "📊 Monitor jobs at: http://YOUR_DROPLET_IP/logs"
echo ""
echo "🔧 Useful Commands:"
echo "   sudo systemctl status video-encoder    # Check service status"
echo "   sudo systemctl restart video-encoder   # Restart service"
echo "   sudo journalctl -u video-encoder -f    # View logs"
echo "   nvidia-smi                             # Check GPU status"
echo ""
echo "⚡ Your NVENC-optimized encoder is ready for 24/7 operation!"
