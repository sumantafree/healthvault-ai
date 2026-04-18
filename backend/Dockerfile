# ============================================================
# HealthVault AI — Backend Dockerfile
# Multi-stage build for production
# ============================================================

FROM python:3.12-slim AS base

# System dependencies (includes tesseract for OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libpq-dev \
    gcc \
    libmupdf-dev \
    mupdf-tools \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependencies ───────────────────────────────────────────────────────────────

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Final image ────────────────────────────────────────────────────────────────

FROM deps AS production

COPY . .

# Non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
