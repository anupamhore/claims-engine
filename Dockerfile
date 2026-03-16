# Dockerfile
# ============================================
# FastAPI Application Container
# ============================================
#
# PURPOSE: Build a Docker image that contains:
#   - Python 3.11 runtime
#   - All Python dependencies (FastAPI, SQLAlchemy, etc.)
#   - Your application code
#
# RESULT: A runnable image that can be deployed anywhere
# (Local Docker, Kubernetes, AWS, etc.)
#
# USAGE:
#   Build: docker build -t claims-engine:latest .
#   Run:   docker run -p 8000:8000 claims-engine:latest
#   Push:  docker push your_registry.com/claims-engine:latest
#

# ============================================
# Stage 1: Builder (Multi-stage build for optimization)
# ============================================
# Multi-stage = reduces final image size
# Stage 1: Install dependencies
# Stage 2: Copy only what's needed (smaller image)

FROM python:3.11-slim as builder

# Set working directory inside container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Create wheels (pre-compiled Python packages)
# Wheels are faster to install than source distributions
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# Stage 2: Runtime (Final container)
# ============================================
# Start fresh with only runtime dependencies (smaller image)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install wheels (no need to compile again)
RUN pip install --no-cache /wheels/*

# ============================================
# Copy Application Code
# ============================================

# Copy entire project directory into container
COPY . .

# ============================================
# Environment Setup
# ============================================

# Set Python to unbuffered output
# (Shows logs immediately, not buffered)
ENV PYTHONUNBUFFERED=1

# Default environment (can be overridden)
ENV APP_ENV=production
ENV LOG_LEVEL=INFO

# ============================================
# Health Check
# ============================================
# Tells Docker how to check if app is healthy

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"
# Every 30 seconds, check if /api/v1/health endpoint responds
# If 3 checks fail, mark container as unhealthy
# Wait 5 seconds before starting checks (app startup time)

# ============================================
# Expose Port
# ============================================

EXPOSE 8000
# Document that container listens on port 8000
# (Doesn't actually expose - docker run -p does that)

# ============================================
# Startup Command
# ============================================
# What runs when container starts

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Command breakdown:
#   uvicorn           = ASGI server to run FastAPI
#   src.api.main:app  = File path + FastAPI app object
#   --host 0.0.0.0    = Listen on all network interfaces (Docker requirement)
#   --port 8000       = Listen on port 8000
#
# Equivalent to: uvicorn src.api.main:app --host 0.0.0.0 --port 8000