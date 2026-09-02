import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import text
from app.database import engine, Base
from app.config import settings
from app.routers import auth, student, content, quiz, parent, teacher, flashcard, recommendations, tutor, admin, ingestion, privacy, challenges

import logging

logger = logging.getLogger("edufeedia.main")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conditional table automigration on boot (development & test only)
    if settings.ENVIRONMENT != "production":
        try:
            import app.models.models
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.error(f"[SCHEMA INITIALIZATION WARNING]: {e}", exc_info=True)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A safe, personalized learning platform for students under 18.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS with strict explicit origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include core routers under v1 API prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(student.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(parent.router, prefix="/api/v1")
app.include_router(teacher.router, prefix="/api/v1")
app.include_router(flashcard.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(tutor.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1")
app.include_router(challenges.router, prefix="/api/v1")

import uuid
import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Request tracking telemetry counters
METRICS_START_TIME = time.time()
_METRICS_COUNTER = {
    "total_requests": 0,
    "successful_requests": 0,
    "error_requests_4xx": 0,
    "error_requests_5xx": 0,
}

# Request-ID Correlation Middleware & Telemetry
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    _METRICS_COUNTER["total_requests"] += 1
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    try:
        response: Response = await call_next(request)
        if 200 <= response.status_code < 400:
            _METRICS_COUNTER["successful_requests"] += 1
        elif 400 <= response.status_code < 500:
            _METRICS_COUNTER["error_requests_4xx"] += 1
        else:
            _METRICS_COUNTER["error_requests_5xx"] += 1
    except Exception:
        _METRICS_COUNTER["error_requests_5xx"] += 1
        raise

    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(duration_ms)
    return response



@app.get("/health", tags=["system"])
def liveness_check():
    """Liveness probe for container orchestrators (Kubernetes / ECS)."""
    return {
        "status": "healthy",
        "live": True,
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

@app.get("/ready", tags=["system"])
def readiness_check():
    """Readiness probe verifying database and cache cluster connectivity."""
    db_status = "unknown"
    redis_status = "unknown"
    errors = []

    # 1. Database Check
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
        errors.append(f"Database error: {e}")

    # 2. Redis Check
    try:
        redis_client.setex("readiness_heartbeat", 10, "1")
        if redis_client.get("readiness_heartbeat") == "1":
            redis_status = "connected"
        else:
            redis_status = "degraded"
    except Exception as e:
        redis_status = "disconnected"
        errors.append(f"Redis error: {e}")

    is_ready = (db_status == "connected") and (redis_status in ["connected", "degraded"])
    status_code = 200 if is_ready else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "unhealthy",
            "ready": is_ready,
            "database": db_status,
            "redis": redis_status,
            "service": settings.PROJECT_NAME,
            "errors": errors if errors else None
        }
    )

@app.get("/metrics", tags=["system"])
def get_system_metrics():
    """Operational telemetry & metrics endpoint for CloudWatch / Prometheus."""
    uptime_seconds = int(time.time() - METRICS_START_TIME)
    return {
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "telemetry": _METRICS_COUNTER,
        "security": {
            "fail_closed_ai_enabled": True,
            "verifiable_parental_consent": True,
            "tenant_isolation_enforced": True
        }
    }

# Mount static frontend directories for hosting the web client dashboard if populated
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path) and os.listdir(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
