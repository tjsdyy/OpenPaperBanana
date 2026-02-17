# syntax=docker/dockerfile:1

# ── Build stage ────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for Pillow / matplotlib
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libgl1 \
        libglib2.0-0 \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY paperbanana/ paperbanana/
COPY api/ api/
COPY mcp_server/ mcp_server/
COPY prompts/ prompts/
COPY data/ data/
COPY configs/ configs/

RUN pip install --no-cache-dir ".[api]"

# ── Runtime stage ──────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -r appuser
WORKDIR /app

# Copy installed packages and application
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/paperbanana paperbanana/
COPY --from=builder /build/api api/
COPY --from=builder /build/mcp_server mcp_server/
COPY --from=builder /build/prompts prompts/
COPY --from=builder /build/data data/
COPY --from=builder /build/configs configs/

# Environment variables for providers (overridden by docker-compose environment)
ENV VLM_PROVIDER=gemini
ENV VLM_MODEL=gemini-2.0-flash-exp
ENV IMAGE_PROVIDER=google_imagen
ENV IMAGE_MODEL=imagen-3.0-generate-001

RUN mkdir -p outputs && chown appuser:appuser outputs

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
