"""
Enforceable Database Consent Verification & Revocation Service.
Implements purpose-specific verifiable guardian consent workflows designed in accordance with DPDP Act 2023 Section 9 principles.
"""

import datetime
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import ConsentRecord, User, StudentProfile
from app.core.age_policy import ChildConsentPolicy, StudentAgePolicy, ProcessingPurpose
from app.core.redis_client import redis_client

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

        # 2. Query persistent database for active or revoked consent records
        record = db.query(ConsentRecord).filter(
            ConsentRecord.student_user_id == student_user.id,
            ConsentRecord.processing_purpose == purpose.value
        ).first()

        now = datetime.datetime.now(datetime.timezone.utc)
        if record:
            if record.status == "ACTIVE":
                if record.expires_at is None or (record.expires_at.replace(tzinfo=datetime.timezone.utc) if record.expires_at.tzinfo is None else record.expires_at) > now:
                    return True
            # Explicitly REVOKED or EXPIRED
            logger.warning(
                f"[CONSENT REVOKED/DENIED] Student: {student_user.id} (Age: {student_age}) has status '{record.status}' "
                f"for purpose: {purpose.value}"
            )
            return False

        # Fallback to verified profile status if granular ConsentRecord was not pre-created
        if profile and profile.parental_consent_status == "GRANTED":
            try:
                auto_record = ConsentRecord(
                    student_user_id=student_user.id,
                    guardian_user_id=None,
                    processing_purpose=purpose.value,
                    status="ACTIVE",
                    verification_method="GUARDIAN_VERIFIED",
                    policy_version="2026.2-DPDP",
                    consent_scope="ALL_CURRICULUM_INTERACTIONS"
                )
                db.add(auto_record)
                db.commit()
            except Exception:
                db.rollback()
            return True

        if profile and profile.parental_consent_status == "REVOKED":
            logger.warning(f"[CONSENT REVOKED] Student: {student_user.id} has parental_consent_status REVOKED.")
            return False

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
            existing.guardian_user_id = guardian_id if guardian_id is not None else existing.guardian_user_id
            existing.consent_scope = scope
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
        Instantly revokes consent for a processing purpose, invalidates downstream caches,
        and purges active in-flight AI and recommendation session contexts.
        """
        record = db.query(ConsentRecord).filter(
            ConsentRecord.student_user_id == student_id,
            ConsentRecord.processing_purpose == purpose
        ).first()

        now = datetime.datetime.now(datetime.timezone.utc)
        if record:
            record.status = "REVOKED"
            record.revoked_at = now
        else:
            record = ConsentRecord(
                student_user_id=student_id,
                guardian_user_id=None,
                processing_purpose=purpose,
                consent_scope=purpose,
                status="REVOKED",
                revoked_at=now
            )
            db.add(record)

        # Invalidate legacy profile status
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        if profile and purpose in (ProcessingPurpose.AI_SOCRATIC_TUTOR.value, ProcessingPurpose.PERSONALIZED_RECOMMENDATIONS.value):
            profile.parental_consent_status = "REVOKED"

        db.commit()

        # Invalidate downstream caches and active sessions in Redis
        try:
            redis_client.delete_pattern(f"tutor:session:{student_id}:*")
            redis_client.delete_pattern(f"rec:feed:{student_id}:*")
            redis_client.delete_pattern(f"ai:session:{student_id}:*")
        except Exception as e:
            logger.error(f"[CACHE PURGE ERROR] Could not purge downstream caches on revocation: {e}")

        logger.info(f"[CONSENT REVOKED] Revoked active consent and purged caches for student {student_id}, purpose: {purpose}")
