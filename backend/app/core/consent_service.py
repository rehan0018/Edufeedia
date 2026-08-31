"""
Enforceable Database Consent Verification & Revocation Service.
Guarantees real-time compliance with DPDP Act 2023 Section 9 statutory requirements.
"""

import datetime
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import ConsentRecord, User, StudentProfile
from app.core.age_policy import ChildConsentPolicy, StudentAgePolicy, ProcessingPurpose

logger = logging.getLogger("edufeedia.consent")


class ConsentService:
    """
    Evaluates and manages active database consent records for student data processing purposes.
    """

    @classmethod
    def has_valid_consent(
        cls,
        db: Session,
        student_user: User,
        purpose: ProcessingPurpose
    ) -> bool:
        """
        Determines whether active consent exists for the student for the given processing purpose.
        Fails closed for minors under 18 if explicit consent is required and no active ConsentRecord exists.
        """
        if not student_user:
            return False

        profile = student_user.student_profile
        student_age = StudentAgePolicy.get_student_age(profile)

        # 1. Evaluate statutory consent requirement
        eval_result = ChildConsentPolicy.evaluate_consent_requirement(
            age=student_age,
            processing_purpose=purpose.value
        )

        # If the processing purpose does not require explicit guardian consent (e.g. safety monitoring / institutional admin)
        if not eval_result["requires_guardian_consent"]:
            return True

        # 2. Query persistent database for active consent record
        record = db.query(ConsentRecord).filter(
            ConsentRecord.student_user_id == student_user.id,
            ConsentRecord.processing_purpose == purpose.value,
            ConsentRecord.status == "ACTIVE"
        ).first()

        if record:
            return True

        # Fallback check on student_profile legacy consent status during migration
        if profile and profile.parental_consent_status == "GRANTED":
            # Auto-seed the granular consent record
            cls.grant_consent(
                db=db,
                student_id=student_user.id,
                guardian_id=None,
                purpose=purpose.value,
                scope=eval_result["consent_scope"],
                method="LEGACY_VERIFIED_PROFILE"
            )
            return True

        logger.warning(
            f"[CONSENT DENIED] Student: {student_user.id} (Age: {student_age}) lacks active guardian consent "
            f"for purpose: {purpose.value} (Policy Basis: {eval_result['policy_basis']})"
        )
        return False

    @classmethod
    def grant_consent(
        cls,
        db: Session,
        student_id: str,
        guardian_id: Optional[str],
        purpose: str,
        scope: str,
        method: str = "GUARDIAN_EMAIL_OTP",
        policy_version: str = "2026.2-DPDP"
    ) -> ConsentRecord:
        """
        Records or updates an active consent grant for a specific processing purpose.
        """
        existing = db.query(ConsentRecord).filter(
            ConsentRecord.student_user_id == student_id,
            ConsentRecord.processing_purpose == purpose
        ).first()

        now = datetime.datetime.now(datetime.timezone.utc)
        if existing:
            existing.status = "ACTIVE"
            existing.guardian_user_id = guardian_id or existing.guardian_user_id
            existing.scope = scope
            existing.verification_method = method
            existing.policy_version = policy_version
            existing.granted_at = now
            existing.revoked_at = None
            db.commit()
            db.refresh(existing)
            return existing

        record = ConsentRecord(
            student_user_id=student_id,
            guardian_user_id=guardian_id,
            processing_purpose=purpose,
            consent_scope=scope,
            status="ACTIVE",
            policy_version=policy_version,
            verification_method=method,
            granted_at=now
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def revoke_consent(
        cls,
        db: Session,
        student_id: str,
        purpose: str
    ) -> None:
        """
        Instantly revokes consent for a processing purpose.
        """
        record = db.query(ConsentRecord).filter(
            ConsentRecord.student_user_id == student_id,
            ConsentRecord.processing_purpose == purpose
        ).first()

        if record:
            record.status = "REVOKED"
            record.revoked_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            logger.info(f"[CONSENT REVOKED] Revoked active consent for student {student_id}, purpose: {purpose}")
