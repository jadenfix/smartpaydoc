#!/bin/bash

# Install Python dependencies
pip install -r requirements-vercel.txt

# Create necessary directories
mkdir -p /var/task/static

# Copy static files
cp -r web/static/* /var/task/static/ 2>/dev/null || :

# Create a Python package if needed
if [ ! -f /var/task/__init__.py ]; then
    touch /var/task/__init__.py
fi
