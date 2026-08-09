import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.config import settings
from app.routers import auth, student, content, quiz, parent, teacher, flashcard

# Create database tables (SQLite automigration on boot for simple local startup)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A safe, personalized learning platform for students under 18.",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME}

# Mount static frontend directories for hosting the web client dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
