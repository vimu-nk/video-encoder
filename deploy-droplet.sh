#!/bin/bash
# DigitalOcean GPU Droplet Deployment Script
# This script sets up the video encoder with NVENC force-enabled

echo "🚀 Setting up Video Encoder on DigitalOcean GPU Droplet"
echo "============================================================"

# Set environment variable to force NVENC detection
export FORCE_NVENC=1
echo "✅ FORCE_NVENC=1 (Enabled)"

# Verify NVENC availability
echo ""
echo "🔍 Verifying NVENC capabilities..."
ffmpeg -hide_banner -encoders | grep nvenc

# Test functionality if available
echo ""
echo "🧪 Testing NVENC functionality..."
python3 test_nvenc.py

echo ""
echo "🎯 Starting video encoder with NVENC enabled..."
echo "Environment: FORCE_NVENC=$FORCE_NVENC"

# Start the application with NVENC forced
# You can run this command on your droplet:
# export FORCE_NVENC=1 && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo ""
echo "📋 To start the encoder manually:"
echo "export FORCE_NVENC=1"
echo "python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "✅ Setup complete!"
