#!/bin/bash
set -e

echo "=== Starting Vercel build process ==="

# Create necessary directories
echo "=== Creating directories ==="
mkdir -p python

# Set Python path
export PYTHONPATH=$PWD/python:$PWD/web:$PWD

# Install Python requirements with specific versions
echo "=== Installing Python packages ==="
pip install --upgrade pip

# Install core dependencies with specific versions to avoid compilation
echo "=== Installing core dependencies ==="
pip install \
    fastapi==0.68.0 \
    uvicorn==0.15.0 \
    python-dotenv==0.19.0 \
    stripe==7.0.0 \
    requests==2.26.0 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    numpy==1.23.5 \
    scikit-learn==1.0.2 \
    sentence-transformers==2.2.2 \
    anthropic==0.7.5 \
    aiohttp==3.8.4 \
    beautifulsoup4==4.11.1 \
    --target=./python \
    --no-cache-dir \
    --no-warn-script-location

# Create a minimal requirements.txt for Vercel runtime
echo "=== Generating requirements.txt ==="
cat > requirements.txt << 'EOL'
fastapi==0.68.0
uvicorn==0.15.0
python-dotenv==0.19.0
stripe==7.0.0
requests==2.26.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
numpy==1.23.5
scikit-learn==1.0.2
sentence-transformers==2.2.2
anthropic==0.7.5
aiohttp==3.8.4
beautifulsoup4==4.11.1
EOL

# Copy necessary files
echo "=== Copying application files ==="
cp -r web/* python/
cp rag_engine.py python/
cp stripe_docs.json python/

# Create __init__.py files to make Python treat directories as packages
echo "=== Creating __init__.py files ==="
touch python/__init__.py

# Make sure the static directory exists
mkdir -p python/static

# Set proper permissions
echo "=== Setting permissions ==="
chmod -R 755 python

echo "=== Build completed successfully ==="
