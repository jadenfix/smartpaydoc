#!/bin/bash
set -e

echo "=== Starting Vercel build process ==="

# Create a clean Python environment
export PYTHONPATH=$PWD/python
mkdir -p python

# Install Python requirements with specific versions that have pre-built wheels
echo "=== Installing Python packages ==="
pip install --upgrade pip

# Install only essential packages with known working versions
echo "=== Installing core dependencies ==="
pip install \
    fastapi==0.68.0 \
    uvicorn==0.15.0 \
    python-dotenv==0.19.0 \
    stripe==7.0.0 \
    requests==2.26.0 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
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
EOL

echo "=== Build completed successfully ==="
