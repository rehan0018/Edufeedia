# Edufeedia Production Deployment & Infrastructure Guide

## 1. Multi-Container Orchestration (`docker-compose.yml`)

Edufeedia is containerized across four core micro-services:
1. **Frontend**: Nginx reverse proxy serving the React 18 production bundle on Port `3000`.
2. **Backend**: FastAPI running behind `uvicorn` on Port `8000`.
3. **Database**: PostgreSQL 16 with `pgvector` extension enabled on Port `5432`.
4. **Cache**: Redis 7 Alpine on Port `6379` for session revocation and OTP rate limiting.

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: edufeedia
      POSTGRES_USER: ${POSTGRES_USER:-edufeedia_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U edufeedia_user -d edufeedia"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      ENVIRONMENT: production
      DATABASE_URL: postgresql://edufeedia_user:${POSTGRES_PASSWORD}@postgres:5432/edufeedia
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## 2. Production Security & Fail-Fast Verification

Before production launch, verify:
* [x] `ENVIRONMENT=production`
* [x] `SECRET_KEY` is a strong cryptographically generated string ($\ge 32$ characters).
* [x] `DATABASE_URL` points to an authenticated RDS / PostgreSQL cluster (SQLite disallowed).
* [x] `REDIS_URL` connects to an active Redis cluster.
* [x] `ALLOWED_ORIGINS` is restricted to trusted domain names (wildcard `*` rejected).
* [x] Non-root execution in Docker images.
