import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.config import settings
from app.routers import auth, student, content, quiz, parent, teacher, flashcard, recommendations, tutor, admin, ingestion, privacy

# Create database tables (SQLite automigration on boot for simple local startup)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A safe, personalized learning platform for students under 18.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

import uuid
import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Request-ID Correlation Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(duration_ms)
    return response

from app.core.logging_config import logger

logger.info(f"Initializing {settings.PROJECT_NAME} backend service...")

@app.get("/health", tags=["system"])
@app.get("/api/health", tags=["system"])
def health_check():
    """Liveness probe for container orchestrators and load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": "production" if "postgres" in settings.DATABASE_URL else "development"
    }

@app.get("/ready", tags=["system"])
@app.get("/api/ready", tags=["system"])
def readiness_check():
    """Readiness probe verifying database connectivity."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "service": settings.PROJECT_NAME
        }
    except Exception as e:
        logger.error(f"[Readiness Failure]: Database check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# Mount static frontend directories for hosting the web client dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
