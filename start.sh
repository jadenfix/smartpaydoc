#!/bin/bash
set -e

# Ensure the static directory exists
mkdir -p /app/static

# Run the FastAPI application
exec uvicorn web.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips="*"
