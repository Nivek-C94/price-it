#!/bin/bash

# Update package lists
apt-get update && apt-get install -y wget unzip

# Install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Clean up
rm google-chrome-stable_current_amd64.deb

# Ensure dependencies are installed
apt-get install -y python3-pip python3-dev build-essential

# Install Python dependencies
pip install -r requirements.txt
