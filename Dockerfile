# Multi-Stage Production Dockerfile for RAGTUNE Enterprise AI Platform
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

# Final Runtime Image
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/ragtune/.local/bin:$PATH

RUN groupadd -g 10001 ragtune && \
    useradd -u 10001 -g ragtune -s /bin/bash -m ragtune

COPY --from=builder /root/.local /home/ragtune/.local
COPY --chown=ragtune:ragtune . .

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["python", "main.py"]
