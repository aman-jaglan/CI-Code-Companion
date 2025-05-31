# CI Code Companion SDK - Production Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt setup.py ./
COPY ci_code_companion_sdk/ ./ci_code_companion_sdk/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov black flake8 mypy

# Copy source code
COPY . .

# Create non-root user for development
RUN useradd -m -u 1000 developer && chown -R developer:developer /app
USER developer

EXPOSE 5000
CMD ["python", "run_dashboard.py"]

# Production stage
FROM base as production

# Copy source code
COPY web_dashboard/ ./web_dashboard/
COPY run_dashboard.py ./
COPY examples/ ./examples/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port (Cloud Run uses PORT env var)
EXPOSE $PORT

# Production server
CMD gunicorn --bind 0.0.0.0:$PORT run_dashboard:app \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --preload 