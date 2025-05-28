#!/bin/bash
set -e

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p /app/static

# Copy static files if they exist
if [ -d "web/static" ]; then
    cp -r web/static/* /app/static/
fi

# Create a Python package if needed
if [ ! -f /var/task/__init__.py ]; then
    touch /var/task/__init__.py
fi
