#!/bin/bash
set -e

# Ensure the static directory exists
mkdir -p /app/static

# Set default port if not specified
PORT=${PORT:-10000}

# Print environment variables for debugging
echo "Starting application with the following environment:"
echo "PORT: $PORT"
echo "PYTHONPATH: $PYTHONPATH"

# Run the FastAPI application
exec uvicorn web.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --log-level debug
