"""
Curriculum Synchronization API Router for EduFeedia.
Provides on-demand and scheduled synchronization of the official NCERT / CBSE syllabus.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.models import User, ContentItem, Quiz
from app.core.security import RoleChecker, get_current_user
from app.curriculum.ncert_sync import NCERTCurriculumSyncEngine

router = APIRouter(prefix="/curriculum", tags=["Curriculum Synchronization"])

@router.post("/sync", response_model=Dict[str, Any])
def trigger_curriculum_sync(
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """Triggers official NCERT/CBSE curriculum and question-bank sync."""
    result = NCERTCurriculumSyncEngine.sync_curriculum(db)
    return result

@router.get("/status", response_model=Dict[str, Any])
def get_curriculum_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns curriculum sync status, versioning info, and question bank statistics."""
    total_lessons = db.query(ContentItem).filter(ContentItem.board == "CBSE").count()
    total_quizzes = db.query(Quiz).count()

    return {
        "curriculum_version": "CBSE-NCERT-2026.2",
        "official_boards_supported": ["CBSE", "ICSE", "NCERT"],
        "total_cbse_lessons": total_lessons,
        "total_assessment_quizzes": total_quizzes,
        "last_sync_status": "synced",
        "auto_sync_cadence": "weekly"
    }
