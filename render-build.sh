#!/bin/bash

set -e  # Exit on error

echo "🚀 Updating pip and installing dependencies..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir --force-reinstall -r requirements.txt

echo "📦 Downloading Chrome binary..."
mkdir -p /opt/render/project/.chrome
wget -O /opt/render/project/.chrome/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip
unzip /opt/render/project/.chrome/chrome.zip -d /opt/render/project/.chrome/
chmod +x /opt/render/project/.chrome/chrome-linux64/chrome

echo "🌐 Setting Chrome path..."
export CHROME_PATH="/opt/render/project/.chrome/chrome-linux64/chrome"
export GOOGLE_CHROME_SHIM="/opt/render/project/.chrome/chrome-linux64/chrome"

# Ensure Botasaurus can find Chrome
ln -sf /opt/render/project/.chrome/chrome-linux64/chrome /usr/bin/google-chrome || true

echo "✅ Build completed successfully."
