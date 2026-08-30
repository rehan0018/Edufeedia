import logging
from typing import Optional, Any, List, Dict
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import User, StudentProfile, parent_student_links, teacher_classes, SchoolClass, ParentalConsentLog
from app.core.security import get_current_user
from app.database import get_db

logger = logging.getLogger("edufeedia.security")

class AccessPolicy:
    """
    Centralized Multi-Tenant & Multi-User Access Control Policy Engine.
    Enforces strict relational boundaries:
    - Student: Private access to their own data only.
    - Parent: Access restricted to verified linked children.
    - Teacher: Access restricted to assigned classes and school tenant.
    - School Admin: Access scoped strictly to their school tenant.
    - Super Admin: Explicit platform-wide audited access.
    """

    @staticmethod
    def log_violation(caller: User, action: str, details: str) -> None:
        """Emits structured security warning for SIEM and audit trails on authorization breaches."""
        logger.warning(
            "[SECURITY ACCESS DENIED] CallerID: %s | Role: %s | SchoolID: %s | Action: %s | Details: %s",
            caller.id, caller.role, caller.school_id, action, details
        )

    @staticmethod
    def can_access_learning(user: User) -> bool:
        """Determines if a user has active permissions to browse learning materials."""
        if user.account_status != "ACTIVE":
            return False
        if user.role in ["teacher", "school_admin", "admin", "super_admin"]:
            return True
        if user.role == "parent":
            return True
        if user.role == "student":
            sp: Optional[StudentProfile] = user.student_profile
            if not sp:
                return False
            if sp.learning_access_status != "ACTIVE":
                return False
            if sp.onboarding_status != "COMPLETED":
                return False
            return True
        return False

    @classmethod
    def has_consent(cls, student: User, scope: str, db: Optional[Session] = None) -> bool:
        """
        Verifies whether student has verified guardian consent for a specific processing scope
        (e.g., 'ai_socratic_tutor', 'analytics_tracking', 'curriculum_access').
        Fails closed if database session is missing.
        """
        sp: Optional[StudentProfile] = student.student_profile
        if not sp:
            return False
        if sp.parental_consent_status == "EXEMPT_ADULT":
            return True
        if sp.parental_consent_status != "GRANTED":
            return False

        if not db:
            # Minor-sensitive processing strictly fails closed without database session
            return False

        latest_consent = db.query(ParentalConsentLog).filter(
            ParentalConsentLog.student_user_id == student.id,
            ParentalConsentLog.consent_status == "granted",
            ParentalConsentLog.revoked_at == None
        ).order_by(ParentalConsentLog.granted_at.desc()).first()

        if latest_consent:
            return scope in (latest_consent.consent_scope or [])
        return sp.parental_consent_status in ["GRANTED", "EXEMPT_ADULT"]

    @classmethod
    def require_consent(cls, caller: User, scope: str, db: Session) -> None:
        """Raises 403 Forbidden if the student caller lacks verified consent for the given scope."""
        if caller.role != "student":
            return
        if not cls.has_consent(caller, scope, db):
            cls.log_violation(caller, f"REQUIRE_CONSENT_{scope.upper()}", f"Missing consent scope: {scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Verified parental consent is required for {scope}."
            )

    @classmethod
    def can_preview_ai_content(cls, user: User) -> bool:
        """Determines if a parent or educator is authorized to preview AI curriculum materials."""
        if user.account_status != "ACTIVE":
            return False
        return user.role in ["parent", "teacher", "school_admin", "admin", "super_admin"]

    @classmethod
    def can_use_ai_tutor(cls, user: User, db: Optional[Session] = None) -> bool:
        """
        AI Socratic Tutor for active student learning strictly requires:
        1. Account status ACTIVE.
        2. Student onboarding status COMPLETED.
        3. Learning access status ACTIVE.
        4. Parental consent scope MUST include 'ai_socratic_tutor'.
        Staff/Admins authorized for monitoring.
        """
        if user.account_status != "ACTIVE":
            return False
        if user.role in ["teacher", "admin", "super_admin", "school_admin"]:
            return True
        if user.role != "student":
            return False

        sp: Optional[StudentProfile] = user.student_profile
        if not sp:
            return False
        if sp.learning_access_status != "ACTIVE":
            return False
        if sp.onboarding_status != "COMPLETED":
            return False

        return cls.has_consent(user, "ai_socratic_tutor", db=db)

    @classmethod
    def can_access_content_item(cls, user: User, item: Any, db: Session) -> bool:
        """
        Validates content access against school tenant boundaries, approval status,
        and student age-suitability band.
        """
        if not item:
            return False
        if not getattr(item, "is_approved", True):
            if user.role not in ["teacher", "school_admin", "admin", "super_admin"]:
                return False

        # School Tenant Check
        item_school = getattr(item, "school_id", None)
        if item_school and user.school_id and item_school != user.school_id:
            if user.role not in ["admin", "super_admin"]:
                return False

        return True

    @classmethod
    def can_view_student_data(cls, caller: User, target_student: User, db: Optional[Session] = None) -> bool:
        """
        Enforces strict tenant and relational isolation for student records:
        - Super Admin: global access
        - School Admin: same school only
        - Teacher: same school only
        - Parent: must have verified link in parent_student_links (is_verified == True)
        - Student: self only
        """
        if caller.account_status != "ACTIVE":
            return False

        if caller.role in ["super_admin", "admin"]:
            return True

        if caller.role in ["school_admin", "teacher"]:
            authorized = caller.school_id is not None and caller.school_id == target_student.school_id
            if not authorized:
                cls.log_violation(caller, "VIEW_STUDENT_DATA", f"Cross-school attempt on student {target_student.id}")
            return authorized

        if caller.role == "parent":
            # If db session is available, perform explicit relational join lookup with is_verified == True
            if db is not None:
                link = db.query(parent_student_links).filter(
                    parent_student_links.c.parent_user_id == caller.id,
                    parent_student_links.c.student_user_id == target_student.id,
                    parent_student_links.c.is_verified == True
                ).first()
                if link:
                    return True
                cls.log_violation(caller, "VIEW_STUDENT_DATA", f"Unverified/unlinked parent access attempt on student {target_student.id}")
                return False

            # Check ORM relationship if db was not provided
            linked_ids = [s.id for s in caller.students_linked] if hasattr(caller, "students_linked") and caller.students_linked else []
            if target_student.id in linked_ids:
                return True

            cls.log_violation(caller, "VIEW_STUDENT_DATA", f"Unlinked parent access attempt on student {target_student.id}")
            return False

        if caller.role == "student":
            authorized = (caller.id == target_student.id)
            if not authorized:
                cls.log_violation(caller, "VIEW_STUDENT_DATA", f"Peer-to-peer data access attempt on student {target_student.id}")
            return authorized

        cls.log_violation(caller, "VIEW_STUDENT_DATA", f"Unauthorized role {caller.role}")
        return False

    @classmethod
    def can_manage_class(cls, caller: User, class_id: str, db: Session) -> bool:
        """Verifies if the caller has pedagogical or administrative authority over a specific class."""
        if caller.role in ["super_admin", "admin"]:
            return True

        school_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
        if not school_class:
            return False

        if caller.role == "school_admin":
            authorized = (caller.school_id is not None and caller.school_id == school_class.school_id)
            if not authorized:
                cls.log_violation(caller, "MANAGE_CLASS", f"School admin cannot manage class {class_id} outside school {caller.school_id}")
            return authorized

        if caller.role == "teacher":
            # Must be assigned to this specific class
            is_assigned = db.query(teacher_classes).filter(
                teacher_classes.c.teacher_user_id == caller.id,
                teacher_classes.c.class_id == class_id
            ).first() is not None

            if not is_assigned:
                cls.log_violation(caller, "MANAGE_CLASS", f"Teacher not assigned to class {class_id}")
            return is_assigned

        cls.log_violation(caller, "MANAGE_CLASS", f"Role {caller.role} cannot manage class")
        return False

    @classmethod
    def can_manage_school(cls, caller: User, target_school_id: str) -> bool:
        """Verifies if the caller is authorized to administer the specified school tenant."""
        if caller.role in ["super_admin", "admin"]:
            return True

        if caller.role == "school_admin":
            authorized = (caller.school_id is not None and caller.school_id == target_school_id)
            if not authorized:
                cls.log_violation(caller, "MANAGE_SCHOOL", f"School admin cannot manage foreign school {target_school_id}")
            return authorized

        cls.log_violation(caller, "MANAGE_SCHOOL", f"Role {caller.role} cannot manage school {target_school_id}")
        return False

    @classmethod
    def can_access_quiz(cls, caller: User, quiz: Any, db: Session) -> bool:
        """
        Validates whether caller can access or submit a specific assessment quiz.
        Guarantees tenant boundaries, content approval, and active learning access.
        """
        if caller.account_status != "ACTIVE":
            return False

        if caller.role in ["admin", "super_admin"]:
            return True

        if caller.role in ["teacher", "school_admin"]:
            if getattr(quiz, "school_id", None) and quiz.school_id != caller.school_id:
                return False
            if not getattr(quiz, "content_item", None):
                return True
            item = quiz.content_item
            if item.school_id is None or item.school_id == caller.school_id:
                return True
            return False

        if caller.role == "student":
            if not cls.can_access_learning(caller):
                return False

            if getattr(quiz, "school_id", None) and quiz.school_id != caller.school_id:
                return False

            if getattr(quiz, "content_item", None):
                item = quiz.content_item
                if not item.is_approved:
                    return False
                if item.school_id is not None and item.school_id != caller.school_id:
                    return False

            return True

        return False

    @staticmethod
    def can_manage_content(user: User) -> bool:
        """Checks if user has permissions to stage or curate curriculum content."""
        return user.role in ["teacher", "school_admin", "admin", "super_admin"] and user.account_status == "ACTIVE"

    @staticmethod
    def can_approve_ingestion(user: User) -> bool:
        """Curriculum staging approval requires verified moderator / educator privileges."""
        return user.role in ["teacher", "school_admin", "admin", "super_admin"]

# --- FASTAPI DEPENDENCY HELPERS ---

def require_learning_access(current_user: User = Depends(get_current_user)) -> User:
    if not AccessPolicy.can_access_learning(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Learning catalog access is restricted for this account state."
        )
    return current_user

def require_ai_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    if not AccessPolicy.can_use_ai_tutor(current_user, db=db):
        sp: Optional[StudentProfile] = current_user.student_profile
        if not sp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student profile not found. Please complete registration."
            )
        if sp.onboarding_status != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI Tutor access restricted: Please complete student profile onboarding first."
            )
        if sp.parental_consent_status == "REVOKED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI Tutor access restricted: Guardian has revoked interactive learning consent."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI Tutor access restricted: Parental consent verification is pending."
        )
    return current_user

def require_staff_access(current_user: User = Depends(get_current_user)) -> User:
    if not AccessPolicy.can_manage_content(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or administrator credentials required."
        )
    return current_user

require_authenticated_user = get_current_user

def require_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student credentials required."
        )
    return current_user

def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["teacher", "school_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or educator credentials required."
        )
    return current_user

def require_school_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["school_admin", "admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="School administrator credentials required."
        )
    return current_user

def require_parent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent or guardian credentials required."
        )
    return current_user
