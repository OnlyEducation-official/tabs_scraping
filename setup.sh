#!/bin/bash

echo "🟢 Updating system packages..."
sudo apt update -y

echo "🟢 Installing Python, pip, and venv..."
sudo apt install -y python3 python3-pip python3-venv

echo "🟢 Creating virtual environment..."
python3 -m venv venv

echo "🟢 Activating virtual environment..."
source venv/bin/activate

echo "🟢 Installing Python dependencies..."
pip install --upgrade pip
pip install playwright beautifulsoup4 python-dotenv psutil

echo "🟢 Installing comprehensive Playwright system dependencies..."
sudo apt install -y \
    wget \
    curl \
    unzip \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgtk-4-1 \
    libxss1 \
    libasound2 \
    libvulkan1 \
    libgraphene-1.0-0 \
    libwoff1 \
    libvpx7 \
    libevent-2.1-7 \
    libopus0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    libflite1 \
    libwebpdemux2 \
    libavif15 \
    libharfbuzz-icu0 \
    libwebpmux3 \
    libenchant-2-2 \
    libsecret-1-0 \
    libhyphen0 \
    libmanette-0.2-0 \
    libx264-163 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1

echo "🟢 Installing Playwright system dependencies using built-in installer..."
playwright install-deps

echo "🟢 Installing Playwright browsers..."
playwright install

echo "🟢 Verifying installation..."
python3 -c "
import sys
sys.path.insert(0, 'venv/lib/python3.12/site-packages')
try:
    from playwright.sync_api import sync_playwright
    print('✅ Playwright Python package installed successfully')
except ImportError as e:
    print('❌ Playwright Python package installation failed:', e)
"

echo "✅ Setup complete. Virtual environment is ready."
echo "📝 To activate the virtual environment, run:"
echo "   source venv/bin/activate"
echo ""
echo "🧪 To test Playwright installation, you can run:"
echo "   python3 -c \"from playwright.sync_api import sync_playwright; print('Playwright is working!')\""