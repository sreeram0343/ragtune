# Multi-Stage Production Dockerfile for RAGTUNE FastAPI Backend Engine
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Final Production Runtime Image
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/ragtune/.local/bin:$PATH

# Security Hardening: Non-root user creation
RUN groupadd -g 10001 ragtune && \
    useradd -u 10001 -g ragtune -s /bin/bash -m ragtune

# Copy dependencies from builder stage
COPY --from=builder /root/.local /home/ragtune/.local

# Copy application source code with correct owner permissions
COPY --chown=ragtune:ragtune . .

# Set working user to non-root
USER 10001:10001

EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Launch uvicorn production server
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
