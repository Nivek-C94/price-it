#!/bin/bash

set -e  # Exit on error

echo "🚀 Updating pip and installing dependencies..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir --force-reinstall -r requirements.txt

echo "📦 Downloading Chrome binary..."
mkdir -p /tmp/google/chrome
wget -O /tmp/google/chrome/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip
unzip /tmp/google/chrome/chrome.zip -d /tmp/google/chrome/
chmod +x /tmp/google/chrome/chrome-linux64/chrome

echo "🌐 Setting Chrome path..."
export CHROME_PATH="/tmp/google/chrome/chrome-linux64/chrome"

echo "✅ Build completed successfully."
