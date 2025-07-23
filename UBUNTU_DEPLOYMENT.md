# Deploying Video Encoder Platform on DigitalOcean Ubuntu

This guide covers deploying the Video Encoder Platform on a DigitalOcean Ubuntu droplet as a production service.

## Prerequisites

-   Ubuntu 20.04+ DigitalOcean droplet
-   SSH access to your droplet
-   Domain name (optional, but recommended)

## Initial Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required Packages

```bash
# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install FFmpeg
sudo apt install ffmpeg -y

# Install Nginx (for reverse proxy)
sudo apt install nginx -y

# Install certbot for SSL (optional)
sudo apt install certbot python3-certbot-nginx -y
```

### 3. Create Application User

```bash
sudo adduser --system --group --home /opt/video-encoder video-encoder
sudo mkdir -p /opt/video-encoder
sudo chown video-encoder:video-encoder /opt/video-encoder
```

## Application Deployment

### 1. Clone Repository

```bash
sudo -u video-encoder git clone https://github.com/your-username/video-encoder.git /opt/video-encoder/app
cd /opt/video-encoder/app
```

### 2. Set Up Python Virtual Environment

```bash
sudo -u video-encoder python3 -m venv /opt/video-encoder/venv
sudo -u video-encoder /opt/video-encoder/venv/bin/pip install -r requirements.txt
```

### 3. Configure Environment

```bash
sudo -u video-encoder cp .env.example .env
sudo -u video-encoder nano .env
```

Add your Bunny CDN credentials:

```env
SOURCE_BUNNY_API_KEY=your_source_api_key
SOURCE_BUNNY_STORAGE_ZONE=your_source_zone
SOURCE_BUNNY_STORAGE_HOST=sg.storage.bunnycdn.com

DEST_BUNNY_API_KEY=your_dest_api_key
DEST_BUNNY_STORAGE_ZONE=your_dest_zone
DEST_BUNNY_STORAGE_HOST=storage.bunnycdn.com
```

### 4. Test Application

```bash
sudo -u video-encoder /opt/video-encoder/venv/bin/python service.py
```

Press Ctrl+C to stop after confirming it works.

## Systemd Service Setup

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/video-encoder.service
```

Copy the service configuration (see below).

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable video-encoder
sudo systemctl start video-encoder
sudo systemctl status video-encoder
```

## Nginx Reverse Proxy Setup

### 1. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/video-encoder
```

Copy the Nginx configuration (see below).

### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/video-encoder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Optional but Recommended)

```bash
sudo certbot --nginx -d your-domain.com
```

## Firewall Configuration

```bash
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable
```

## Monitoring and Logs

### View Service Logs

```bash
sudo journalctl -u video-encoder -f
```

### Service Management

```bash
sudo systemctl start video-encoder     # Start
sudo systemctl stop video-encoder      # Stop
sudo systemctl restart video-encoder   # Restart
sudo systemctl status video-encoder    # Status
```

## Maintenance Scripts

Create useful management scripts in `/opt/video-encoder/`:

-   `deploy.sh` - For easy updates
-   `backup.sh` - For backing up logs and configs
-   `monitor.sh` - For health checking

## Security Considerations

1. **Firewall**: Only allow necessary ports (22, 80, 443)
2. **User permissions**: Run service as non-root user
3. **SSL**: Use HTTPS in production
4. **Updates**: Keep system and dependencies updated
5. **Monitoring**: Set up log monitoring and alerts
6. **Backups**: Regular backups of configuration and logs

## Scaling Considerations

For high-volume encoding:

1. **Use object storage**: Mount external storage for temporary files
2. **Queue system**: Implement Redis/RabbitMQ for job queuing
3. **Multiple workers**: Run multiple encoding processes
4. **Load balancing**: Use multiple droplets behind a load balancer
5. **Database**: Move from in-memory storage to PostgreSQL/MySQL

## Troubleshooting

### Service won't start

```bash
sudo journalctl -u video-encoder --no-pager
```

### Check FFmpeg installation

```bash
ffmpeg -version
```

### Test Bunny CDN connectivity

```bash
sudo -u video-encoder /opt/video-encoder/venv/bin/python test_navigation.py
```

### Check disk space

```bash
df -h
du -sh /opt/video-encoder/app/input/*
du -sh /opt/video-encoder/app/output/*
```

### Monitor resource usage

```bash
htop
sudo iotop
```
