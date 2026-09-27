"""
Educational Discovery and Intelligence API Router.
Exposes federated candidate search, authority registry, concept-check grading,
and mastery index updates for Edufeedia's Learning Navigator.
"""

import time
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database import get_db
from app.config import settings
from app.core.security import is_token_revoked
from app.models.models import User, DiscoveryQueryLog, StudentMasteryHistory
from app.schemas.schemas import (
    DiscoverySearchResponse, QuizSubmitRequest, QuizSubmitResponse,
    ResourceEngagementRequest
)
from app.discovery.pipeline import DiscoveryPipeline
from app.discovery.learning_loop import LearningLoopManager
from app.discovery.source_registry import SourceAuthorityRegistry
from app.discovery.resource_quality import ScoringPolicy

router = APIRouter(prefix="/discovery", tags=["discovery"])


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extracts authenticated user if Bearer token is provided and valid.
    Returns None for guest/unauthenticated users without throwing 401.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        if is_token_revoked(token):
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
        user = db.query(User).filter(User.email == email).first()
        if user and user.account_status == "ACTIVE":
            return user
        return None
    except (JWTError, Exception):
        return None


@router.get("/search", response_model=DiscoverySearchResponse)
def search_educational_resources(
    q: str = Query(..., min_length=2, max_length=250, description="Natural language educational query"),
    grade: Optional[int] = Query(None, ge=1, le=12, description="Target student grade level (1-12)"),
    board: Optional[str] = Query(None, description="Target curriculum board (e.g., CBSE, ICSE)"),
    depth: Optional[str] = Query(None, description="Pedagogical depth: quick_summary, standard, deep_dive"),
    format_pref: Optional[str] = Query(None, description="Preferred format: animation, video, reading, sim"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Intelligent Educational Discovery Pipeline.
    Federates candidate discovery across Verified Catalogs, NCERT Textbooks, PhET Simulations,
    and Vetted Creator Channels.
    Applies identity validation, safety gating, age gating, source authority tiers,
    instrumented 10-factor quality scoring, and personalized mastery reranking.
    """
    start_time = time.time()

    # Prepend grade or board context if passed as explicit URL params
    augmented_query = q
    if grade and f"class {grade}" not in q.lower() and f"grade {grade}" not in q.lower():
        augmented_query = f"{augmented_query} Class {grade}"
    if board and board.lower() not in q.lower():
        augmented_query = f"{augmented_query} {board}"

    # Execute discovery through authoritative pipeline
    response = DiscoveryPipeline.execute_discovery(
        db=db,
        query=augmented_query,
        student_user=current_user
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Persist audit search log asynchronously/safely
    try:
        top_res = response.best_match
        log_entry = DiscoveryQueryLog(
            student_user_id=current_user.id if current_user else None,
            raw_query=q,
            interpreted_intent=response.interpreted_intent.model_dump(),
            results_count=len(response.all_ranked_resources),
            top_resource_id=top_res.id if top_res else None,
            top_resource_score=top_res.quality_score if top_res else None,
            response_time_ms=elapsed_ms
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()

    return response


@router.post("/quiz-submit", response_model=QuizSubmitResponse)
def submit_concept_check(
    body: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Submits student responses for a 5-question diagnostic concept check.
    Evaluates answers, computes knowledge delta (+15% mastery gain), updates student's
    TopicMastery index, and records audit history in the closed learning loop.
    """
    return LearningLoopManager.evaluate_quiz_submission(
        db=db,
        student_user=current_user,
        request=body
    )


@router.post("/resource-engagement")
def log_resource_engagement(
    body: ResourceEngagementRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Records student dwell time and completed learning sessions on discovered resources.
    Awards engagement XP and feeds back into the student recommendation model.
    """
    return LearningLoopManager.record_resource_engagement(
        db=db,
        student_user=current_user,
        request=body
    )


@router.get("/sources")
def list_educational_sources():
    """
    Returns the Authoritative Educational Source Registry.
    Lists trusted institutions and vetted creators across Authority Tiers A, B, C, D, and E.
    """
    sources = SourceAuthorityRegistry.list_sources()
    return {
        "total_registered_sources": len(sources),
        "sources": sources,
        "tier_definitions": {
            "TIER_A": "Official Curriculum Authorities & Government Publishers (NCERT, CBSE, State Boards)",
            "TIER_B": "Accredited Universities, Global Non-Profits, and Peer-Reviewed OER (Khan Academy, PhET, MIT OpenCourseWare)",
            "TIER_C": "Vetted Educational Content Creators with Proven Pedagogy (3Blue1Brown, Veritasium, Physics Wallah, MinutePhysics)",
            "TIER_D": "Open Public Platforms & Unvetted User-Generated Content (Requires Human Moderation)",
            "TIER_E": "Unverified, Promotional, Commercial Content or High-Risk Sources (Strictly Blocked)"
        }
    }


@router.get("/scoring-policy")
def get_scoring_policy():
    """
    Returns the versioned scoring policy weights and thresholds.
    Ensures transparent, tunable algorithm governance (v1.0).
    """
    default_policy = ScoringPolicy()
    return {
        "policy_version": default_policy.policy_version,
        "weights": default_policy.weights,
        "safety_threshold": default_policy.safety_threshold,
        "curriculum_match_threshold": default_policy.curriculum_match_threshold,
        "age_gate_strict": default_policy.age_gate_strict,
        "description": "Edufeedia v1.0 Multi-Factor Educational Quality & Pedagogical Alignment Scoring Policy"
    }


@router.get("/mastery-history")
def get_student_mastery_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns the mastery progression timeline for the authenticated student.
    Shows topic evolution and learning gains over time.
    """
    if not current_user:
        return {"student_id": None, "history": []}

    records = db.query(StudentMasteryHistory).filter(
        StudentMasteryHistory.student_user_id == current_user.id
    ).order_by(StudentMasteryHistory.created_at.desc()).limit(limit).all()

    return {
        "student_id": current_user.id,
        "total_records": len(records),
        "history": [
            {
                "id": r.id,
                "topic": r.topic,
                "subject": r.subject,
                "prior_mastery": float(r.prior_mastery or 0.0),
                "new_mastery": float(r.new_mastery or 0.0),
                "learning_gain": float(r.learning_gain or 0.0),
                "quiz_score_pct": float(r.quiz_score_pct) if r.quiz_score_pct is not None else None,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }
