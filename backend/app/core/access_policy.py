import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import User, StudentProfile, parent_student_links, teacher_classes, SchoolClass
from app.core.security import get_current_user

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
        if user.role in ["teacher", "school_admin", "admin", "super_admin"]:
            return True
        if user.role == "student":
            return True
        if user.role == "parent":
            return True
        return False

    @staticmethod
    def can_use_ai_tutor(user: User) -> bool:
        """
        AI Socratic Tutor strictly requires:
        1. Educators & Admins: authorized by default.
        2. Parents: authorized to inspect and preview learning materials.
        3. Students: onboarding MUST be COMPLETED and parental consent MUST be GRANTED or EXEMPT_ADULT.
        """
        if user.role in ["teacher", "admin", "super_admin", "school_admin"]:
            return True
        if user.role == "parent":
            return True
        if user.role == "student":
            sp: Optional[StudentProfile] = user.student_profile
            if not sp:
                return False
            if sp.onboarding_status != "COMPLETED":
                return False
            if sp.parental_consent_status not in ["GRANTED", "EXEMPT_ADULT"]:
                return False
            return True
        return False

    @classmethod
    def can_view_student_data(cls, caller: User, target_student: User, db: Optional[Session] = None) -> bool:
        """
        Enforces strict tenant and relational isolation for student records:
        - Super Admin: global access
        - School Admin: same school only
        - Teacher: same school only
        - Parent: must have verified link in parent_student_links
        - Student: self only
        """
        if caller.role in ["super_admin", "admin"]:
            return True

        if caller.role in ["school_admin", "teacher"]:
            authorized = caller.school_id is not None and caller.school_id == target_student.school_id
            if not authorized:
                cls.log_violation(caller, "VIEW_STUDENT_DATA", f"Cross-school attempt on student {target_student.id}")
            return authorized

        if caller.role == "parent":
            # Check ORM relationship first
            linked_ids = [s.id for s in caller.students_linked] if hasattr(caller, "students_linked") and caller.students_linked else []
            if target_student.id in linked_ids:
                return True

            # If db session is available, perform explicit relational join lookup
            if db is not None:
                link = db.query(parent_student_links).filter(
                    parent_student_links.c.parent_user_id == caller.id,
                    parent_student_links.c.student_user_id == target_student.id
                ).first()
                if link:
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

    @staticmethod
    def can_manage_content(user: User) -> bool:
        """Only educational staff and administrators can manage curriculum items."""
        return user.role in ["teacher", "school_admin", "admin", "super_admin"]

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

def require_ai_access(current_user: User = Depends(get_current_user)) -> User:
    if not AccessPolicy.can_use_ai_tutor(current_user):
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
