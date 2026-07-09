# ==============================================================================
# Stage 1: Build the React/Vite frontend
# ==============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
ENV NODE_OPTIONS=--max-old-space-size=4096

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Python backend with ML/AI dependencies
# ==============================================================================
FROM python:3.11-slim AS backend

# Install system dependencies required by audio/ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    poppler-utils \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy the built frontend static files into the expected location
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose the FastAPI port
EXPOSE 8000

# Environment variables (override via docker run -e or docker-compose env_file)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEIA_ASR_DEVICE=cpu

# Run the FastAPI server. Railway injects PORT at runtime.
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
