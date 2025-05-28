# Build stage
FROM python:3.9-slim as builder

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install minimal dependencies first
COPY requirements-minimal.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Copy and install full requirements if they exist
COPY requirements.txt .
RUN if [ -f "requirements.txt" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/cache && \
    chmod 777 /app/cache

# Expose the port the app runs on
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:10000/health || exit 1

# Command to run the application
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "10000", "--proxy-headers"]
