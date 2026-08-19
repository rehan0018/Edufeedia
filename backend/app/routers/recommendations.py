from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.models import User, StudentProfile
from app.schemas.schemas import (
    RecommendationFeedOut, InteractionCreate, InteractionOut,
    SafetyCheckRequest, SafetyReportOut
)
from app.core.security import RoleChecker
from app.safety.engine import SafetyEngine
from app.learning.feedback import log_interaction
from app.recommender.hybrid import recommender_instance

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/feed", response_model=RecommendationFeedOut)
def get_personalized_feed(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Returns the multi-stage personalized recommendation feed with explainability scores.
    """
    feed = recommender_instance.get_personalized_recommendations(
        db=db,
        student_id=current_user.id,
        limit=4
    )
    return feed

@router.post("/interaction", response_model=InteractionOut, status_code=status.HTTP_201_CREATED)
def record_interaction(
    interaction_in: InteractionCreate,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Records an implicit interaction (view, click, like, bookmark, dwell time, skip) to train collaborative feedback.
    """
    from app.models.models import ContentItem
    item = db.query(ContentItem).filter(
        ContentItem.id == interaction_in.content_item_id,
        ContentItem.is_approved == True
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content item not found or not approved for student interaction"
        )

    interaction = log_interaction(
        db=db,
        user_id=current_user.id,
        content_item_id=interaction_in.content_item_id,
        interaction_type=interaction_in.interaction_type,
        dwell_time_seconds=interaction_in.dwell_time_seconds or 0
    )

    return interaction

@router.post("/inspect-safety", response_model=SafetyReportOut)
def inspect_content_safety(
    request: SafetyCheckRequest,
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Evaluates arbitrary content against the Safety Engine (Rules, Transformer Heuristics, Under-18 Policy).
    """
    audit = SafetyEngine.audit_content(
        title=request.title,
        description=request.description or "",
        target_age=request.target_age_group or 16
    )
    return audit
