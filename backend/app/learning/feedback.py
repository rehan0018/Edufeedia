from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import datetime

from app.models.models import UserInteraction, ContentItem, StudentProfile

# Explicit weights for implicit student interactions
INTERACTION_WEIGHTS: Dict[str, float] = {
    "completed": 5.0,
    "quiz_completed": 5.0,
    "watched_80": 4.0,
    "bookmark": 4.0,
    "like": 3.0,
    "click": 2.0,
    "view": 1.0,
    "skip": -2.0
}

def log_interaction(
    db: Session,
    user_id: str,
    content_item_id: str,
    interaction_type: str,
    dwell_time_seconds: int = 0
) -> UserInteraction:
    """
    Records an implicit or explicit user interaction in the recommendation database.
    """
    weight = INTERACTION_WEIGHTS.get(interaction_type, 1.0)
    
    interaction = UserInteraction(
        user_id=user_id,
        content_item_id=content_item_id,
        interaction_type=interaction_type,
        weight=weight,
        dwell_time_seconds=dwell_time_seconds
    )
    db.add(interaction)

    # Increment view/like counters on content item
    content = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    if content:
        if interaction_type in ["view", "click"]:
            content.view_count += 1
        elif interaction_type == "like":
            content.like_count += 1

    db.commit()
    db.refresh(interaction)
    return interaction

def get_user_behavioral_profile(db: Session, user_id: str) -> Dict[str, float]:
    """
    Calculates normalized subject/topic preference affinity scores based on past user interactions.
    Positive feedback (completions, likes, bookmarks) increases subject weight; skips decrease it.
    """
    interactions = db.query(UserInteraction).filter(UserInteraction.user_id == user_id).all()
    if not interactions:
        return {}

    subject_scores: Dict[str, float] = {}
    for inter in interactions:
        if inter.content_item:
            subj = inter.content_item.subject
            w = float(inter.weight)
            subject_scores[subj] = subject_scores.get(subj, 0.0) + w

    # Normalize between 0.0 and 1.0
    if not subject_scores:
        return {}

    max_score = max(abs(s) for s in subject_scores.values()) or 1.0
    normalized_profile = {subj: round(score / max_score, 3) for subj, score in subject_scores.items()}
    return normalized_profile
