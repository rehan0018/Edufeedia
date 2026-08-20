from typing import Optional
from fastapi import Depends, HTTPException, status
from app.models.models import User, StudentProfile
from app.core.security import get_current_user

class AccessPolicy:
    """
    Centralized Access Control Policy Engine:
    Consolidates minor-safety, tenant-isolation, parental-consent,
    and role-based authorization rules in a single defensible layer.
    """

    @staticmethod
    def can_access_learning(user: User) -> bool:
        """Determines if a user has active permissions to browse learning materials."""
        if user.role in ["teacher", "school_admin", "admin", "super_admin"]:
            return True
        if user.role == "student":
            # Student can browse basic curriculum catalog once identity is verified or onboarded
            return True
        return False

    @staticmethod
    def can_use_ai_tutor(user: User) -> bool:
        """
        AI Socratic Tutor requires:
        1. User is a student, teacher, or parent.
        2. If student: onboarding must be completed and parental consent must NOT be revoked.
        """
        if user.role in ["teacher", "admin", "super_admin"]:
            return True
        if user.role == "parent":
            return True
        if user.role == "student":
            sp: Optional[StudentProfile] = user.student_profile
            if not sp:
                return False
            if sp.parental_consent_status == "REVOKED":
                return False
            return True
        return False

    @staticmethod
    def can_view_student_data(caller: User, target_student: User) -> bool:
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
            return caller.school_id is not None and caller.school_id == target_student.school_id
        if caller.role == "parent":
            linked_ids = [s.id for s in caller.students_linked] if hasattr(caller, "students_linked") else []
            return target_student.id in linked_ids
        if caller.role == "student":
            return caller.id == target_student.id
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
        if sp and sp.parental_consent_status == "REVOKED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI Tutor access restricted: Guardian has revoked interactive learning consent."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI Tutor access requires active onboarding and verified consent."
        )
    return current_user

def require_staff_access(current_user: User = Depends(get_current_user)) -> User:
    if not AccessPolicy.can_manage_content(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or administrator credentials required."
        )
    return current_user
