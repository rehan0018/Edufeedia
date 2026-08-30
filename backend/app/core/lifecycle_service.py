import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import User, StudentProfile, ParentalConsentLog

logger = logging.getLogger(__name__)

class StudentLifecycleState:
    REGISTERED = "REGISTERED"
    ONBOARDING_PENDING = "ONBOARDING_PENDING"
    ONBOARDING_COMPLETED = "ONBOARDING_COMPLETED"
    CONSENT_PENDING = "CONSENT_PENDING"
    CONSENT_GRANTED = "CONSENT_GRANTED"
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"

class StudentLifecycleService:
    """
    Finite State Machine managing student lifecycle, identity transitions,
    and verified guardian consent states without uncontrolled route mutation.
    """

    @classmethod
    def complete_onboarding(
        cls,
        db: Session,
        user_id: str,
        grade_level: int,
        board: str,
        date_of_birth: datetime.date,
        interests: list
    ) -> Dict[str, Any]:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if not profile:
            raise ValueError("Student profile not found.")

        profile.grade_level = grade_level
        profile.board = board
        profile.date_of_birth = date_of_birth
        profile.interests = interests
        profile.onboarding_status = "COMPLETED"

        # If age >= 18, adult exemption applies
        from app.core.age_policy import AgePolicyService
        age = AgePolicyService.calculate_age(date_of_birth)
        if age >= 18:
            profile.parental_consent_status = "EXEMPT_ADULT"
            profile.learning_access_status = "ACTIVE"
        else:
            if profile.parental_consent_status != "GRANTED":
                profile.parental_consent_status = "PENDING"
                profile.learning_access_status = "RESTRICTED"

        db.commit()
        return {
            "status": "success",
            "onboarding_status": profile.onboarding_status,
            "consent_status": profile.parental_consent_status,
            "learning_access_status": profile.learning_access_status
        }

    @classmethod
    def grant_consent(
        cls,
        db: Session,
        student_id: str,
        parent_user_id: Optional[str],
        parent_email: str,
        verification_method: str = "email_otp",
        consent_scopes: Optional[list] = None
    ) -> Dict[str, Any]:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        if not profile:
            raise ValueError("Student profile not found.")

        profile.parental_consent_status = "GRANTED"
        profile.learning_access_status = "ACTIVE"

        scopes = consent_scopes or ["curriculum_access", "ai_socratic_tutor", "analytics_tracking", "personalization"]

        # Append to audit log
        log = ParentalConsentLog(
            student_user_id=student_id,
            parent_user_id=parent_user_id,
            parent_email=parent_email,
            consent_status="granted",
            verification_method=verification_method,
            consent_scope=scopes,
            granted_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(log)
        db.commit()

        return {
            "status": "consent_granted",
            "student_id": student_id,
            "scopes": scopes,
            "learning_access_status": profile.learning_access_status
        }

    @classmethod
    def revoke_consent(
        cls,
        db: Session,
        student_id: str,
        parent_email: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        if not profile:
            raise ValueError("Student profile not found.")

        profile.parental_consent_status = "REVOKED"
        profile.learning_access_status = "RESTRICTED"

        log = ParentalConsentLog(
            student_user_id=student_id,
            parent_email=parent_email,
            consent_status="revoked",
            verification_method="parent_portal",
            revoked_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(log)
        db.commit()

        return {
            "status": "consent_revoked",
            "student_id": student_id,
            "learning_access_status": "RESTRICTED"
        }
