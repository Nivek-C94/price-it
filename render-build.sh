#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Download a pre-built Chrome binary
mkdir -p /opt/google/chrome
wget -O /opt/google/chrome/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip
unzip /opt/google/chrome/chrome.zip -d /opt/google/chrome/
chmod +x /opt/google/chrome/chrome-linux64/chrome

# Set Chrome binary path
export CHROME_PATH="/opt/google/chrome/chrome-linux64/chrome"