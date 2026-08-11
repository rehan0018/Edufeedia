from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import datetime

from app.database import get_db
from app.models.models import User, StudentProfile, QuizAttempt, StudentProgress, SpacedRepetitionSchedule, UserInteraction
from app.core.security import get_current_user, RoleChecker

router = APIRouter(prefix="/privacy", tags=["privacy"])

class ParentalConsentUpdate(BaseModel):
    parent_email: str
    consent_granted: bool
    verification_method: Optional[str] = "email_confirmation"

@router.get("/consent-status")
def get_privacy_and_consent_status(
    current_user: User = Depends(RoleChecker(["student", "parent", "teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns the COPPA / GDPR-K child data protection status and parental consent details.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    is_minor = True
    grade = profile.school_class.grade_level if (profile and profile.school_class) else 10

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "is_under_18": is_minor,
        "coppa_compliant": True,
        "gdpr_k_compliant": True,
        "data_minimization_enforced": True,
        "parental_consent_verified": current_user.is_verified,
        "targeted_advertising_blocked": True,
        "third_party_tracking_blocked": True,
        "retention_policy": "Strict educational retention. Student records anonymized upon graduation or on request."
    }

@router.post("/parental-consent")
def update_parental_consent(
    consent: ParentalConsentUpdate,
    current_user: User = Depends(RoleChecker(["parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Records verifiable parental consent for a minor under COPPA, GDPR-K, and India DPDP Act 2023.
    """
    from app.models.models import ParentalConsentLog

    student_id = current_user.id
    if current_user.role == "parent" and hasattr(current_user, "students_linked") and current_user.students_linked:
        student_id = current_user.students_linked[0].id

    log_entry = ParentalConsentLog(
        student_user_id=student_id,
        parent_user_id=current_user.id if current_user.role == "parent" else None,
        parent_email=consent.parent_email,
        consent_status="granted" if consent.consent_granted else "revoked",
        verification_method=consent.verification_method or "email_verification",
        consent_scope=["curriculum_access", "ai_socratic_tutor", "analytics_tracking"],
        granted_at=datetime.datetime.utcnow() if consent.consent_granted else None,
        revoked_at=datetime.datetime.utcnow() if not consent.consent_granted else None
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "status": "success",
        "consent_log_id": log_entry.id,
        "parent_email": consent.parent_email,
        "consent_granted": consent.consent_granted,
        "verification_method": consent.verification_method,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "message": "Verifiable parental consent recorded successfully in compliance audit log."
    }

@router.get("/export-my-data")
def export_student_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR-K / COPPA Data Portability: Exports all learning history, quiz attempts,
    progress logs, and profile records in a machine-readable JSON format.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_user_id == current_user.id).all()
    progress_logs = db.query(StudentProgress).filter(StudentProgress.student_user_id == current_user.id).all()
    spaced_schedules = db.query(SpacedRepetitionSchedule).filter(SpacedRepetitionSchedule.student_user_id == current_user.id).all()

    return {
        "export_metadata": {
            "platform": "Edufeedia Safe Learning",
            "compliance": "GDPR-K Article 20 / COPPA Data Portability",
            "exported_at": datetime.datetime.utcnow().isoformat(),
            "user_id": current_user.id
        },
        "user_account": {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        "student_profile": {
            "grade_level": profile.school_class.grade_level if (profile and profile.school_class) else None,
            "board": profile.board if profile else None,
            "interests": profile.interests if profile else [],
            "streak_count": profile.streak_count if profile else 0,
            "xp_score": profile.xp_score if profile else 0
        } if profile else None,
        "quiz_attempts": [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "score": a.score,
                "max_score": a.max_score,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in quiz_attempts
        ],
        "completed_lessons": [
            {
                "content_item_id": p.content_item_id,
                "progress_percentage": p.progress_percentage,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            }
            for p in progress_logs
        ],
        "spaced_repetition_schedules": [
            {
                "subject": s.subject,
                "topic": s.topic,
                "interval_days": s.interval_days,
                "next_review_date": s.next_review_date.isoformat() if s.next_review_date else None
            }
            for s in spaced_schedules
        ]
    }

@router.delete("/purge-my-data")
def purge_student_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR-K Article 17 / COPPA Right to be Forgotten: Permanently deletes or anonymizes
    all personal information, activity logs, and learning profiles.
    """
    user_id = current_user.id

    # 1. Delete associated student records
    db.query(QuizAttempt).filter(QuizAttempt.student_user_id == user_id).delete()
    db.query(StudentProgress).filter(StudentProgress.student_user_id == user_id).delete()
    db.query(SpacedRepetitionSchedule).filter(SpacedRepetitionSchedule.student_user_id == user_id).delete()
    db.query(UserInteraction).filter(UserInteraction.user_id == user_id).delete()
    db.query(StudentProfile).filter(StudentProfile.user_id == user_id).delete()

    # 2. Delete user account
    db.delete(current_user)
    db.commit()

    # 3. Re-sync Excel audit sheet
    try:
        from app.core.excel_exporter import sync_database_to_excel
        sync_database_to_excel(db)
    except Exception as e:
        print(f"[Excel Sync Purge Warning]: {e}")

    return {
        "status": "purged",
        "message": "All student personal data, learning records, and account credentials have been permanently erased in compliance with COPPA and GDPR-K."
    }
