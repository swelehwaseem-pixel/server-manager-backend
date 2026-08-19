# --- STAGE 1: Builder (Compiles dependencies) ---
FROM python:3.11-slim AS builder
WORKDIR /build

# Install build tools (required for some Python native packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- STAGE 2: Production Runner ---
FROM python:3.11-slim AS runner

# 👤 Create a non-root user (UID 1000) to run the app securely
# Also add to 'systemd-journal' group (GID 999) to read host logs if needed
RUN addgroup --gid 1000 appuser && \
    adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser && \
    adduser appuser systemd-journal

WORKDIR /app

# 📦 Install runtime system dependencies (journalctl for live logs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    systemd \
    && rm -rf /var/lib/apt/lists/*

# 📂 Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# 📄 Copy application source code
COPY ./app ./app

# 🔧 Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# 🌍 Set default timezone (recommended for log timestamps)
ENV TZ=UTC

# 🔑 Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# 🩺 Healthcheck (requires a "/health" endpoint in main.py - see note below)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# 🚀 Start Gunicorn with dynamic workers and graceful timeouts
# WEB_CONCURRENCY = number of CPU cores * 2 + 1 (auto-calculated via environment)
# If not set, defaults to 2 to avoid memory bloat on small VMs.
CMD ["sh", "-c", "gunicorn app.main:app \
    -w ${WEB_CONCURRENCY:-2} \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30"]
