# Dockerfile for SchemeSaathi Backend API
# Python 3.11 with OpenMP support for FAISS & PyTorch
FROM python:3.11-slim

# Prevent Python from writing bytecode and enable immediate log streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# Install system dependencies
# libgomp1 is strictly required by FAISS and PyTorch for OpenMP multithreading on Linux
# curl is required for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (optimizing Docker layer caching)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# ==============================================================================
# Pre-download the multilingual sentence-transformers embedding model during build
# Ensures zero cold-start delay and eliminates Hugging Face Hub dependency at runtime
# ==============================================================================
RUN python -c "from sentence_transformers import SentenceTransformer; print('Pre-downloading multilingual-e5-small model...'); SentenceTransformer('intfloat/multilingual-e5-small'); print('Model pre-download complete!')"

# Copy backend application package
COPY backend/app /app/app

# Ensure data directories exist for volume mounting
RUN mkdir -p /app/data/raw /app/data/index

# Expose FastAPI default port
EXPOSE 8000

# Healthcheck testing the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server (uses $PORT from environment if provided by Render/Cloud Run, defaults to 8000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
