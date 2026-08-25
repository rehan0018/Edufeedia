# ==============================================================================
# Edufeedia Production Dockerfile
# Multi-stage secure build for FastAPI backend
# ==============================================================================

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Production Image
FROM python:3.12-slim

WORKDIR /app

# Create non-root unprivileged app user for under-18 container security
RUN groupadd -r edufeedia && useradd -r -g edufeedia edufeedia

COPY --from=builder /root/.local /home/edufeedia/.local
ENV PATH=/home/edufeedia/.local/bin:$PATH

COPY --chown=edufeedia:edufeedia . /app
RUN chmod +x /app/entrypoint.sh

USER edufeedia

EXPOSE 8000

ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
