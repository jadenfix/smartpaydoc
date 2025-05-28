#!/bin/bash
set -e

# Install system dependencies required for Python packages
apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
pip install --upgrade pip
pip install -r api/requirements.in --target=./python

# Create a minimal requirements.txt for Vercel
echo "fastapi==0.68.0" > requirements.txt
echo "uvicorn==0.15.0" >> requirements.txt
echo "python-multipart==0.0.5" >> requirements.txt
echo "jinja2==3.0.0" >> requirements.txt
echo "python-dotenv==0.19.0" >> requirements.txt
echo "stripe==7.0.0" >> requirements.txt
echo "requests==2.26.0" >> requirements.txt
echo "numpy==1.23.5" >> requirements.txt
echo "scikit-learn==1.0.2" >> requirements.txt
echo "pydantic==1.8.2" >> requirements.txt
echo "python-jose[cryptography]==3.3.0" >> requirements.txt
echo "passlib[bcrypt]==1.7.4" >> requirements.txt
echo "sentence-transformers==2.2.2" >> requirements.txt
echo "anthropic==0.7.5" >> requirements.txt
