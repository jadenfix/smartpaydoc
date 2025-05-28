#!/bin/bash
set -e

# Print environment for debugging
echo "=== Build Environment ==="
python --version
pip --version

# Install Python dependencies with verbose output
echo "=== Installing Dependencies ==="
pip install --upgrade pip
pip install --no-cache-dir --upgrade wheel setuptools
pip install --no-cache-dir -r requirements.txt

# Create necessary directories
echo "=== Setting Up Directories ==="
mkdir -p /app/static

# Copy static files if they exist
if [ -d "web/static" ]; then
    echo "=== Copying Static Files ==="
    cp -r web/static/* /app/static/
fi

# Verify installation
echo "=== Verifying Installation ==="
pip freeze

# Create cache directory
mkdir -p /app/cache
chmod 777 /app/cache

echo "=== Build Completed Successfully ==="
