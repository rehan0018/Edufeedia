"""
Role-Based Permission Matrix (RBAC).
Defines granular platform permissions and maps system roles to explicit permission sets.
"""

from enum import Enum
from typing import Set, Dict, Optional


class Permission(str, Enum):
    # Student Learning Permissions
    ACCESS_CURRICULUM = "access_curriculum"
    USE_AI_TUTOR = "use_ai_tutor"
    TAKE_ASSESSMENT = "take_assessment"
    VIEW_OWN_PROGRESS = "view_own_progress"

    # Parent / Guardian Permissions
    VIEW_CHILD_PROGRESS = "view_child_progress"
    MANAGE_CHILD_CONSENT = "manage_child_consent"
    CONFIGURE_SAFETY_CONTROLS = "configure_safety_controls"

    # Teacher / Educator Permissions
    MANAGE_ASSIGNED_CLASSES = "manage_assigned_classes"
    VIEW_CLASS_ANALYTICS = "view_class_analytics"
    AUTHOR_CUSTOM_QUIZ = "author_custom_quiz"
    TRIGGER_AI_QUIZ_GEN = "trigger_ai_quiz_gen"
    FLAG_CONTENT_SAFETY = "flag_content_safety"

    # School Administrator Permissions
    MANAGE_SCHOOL_CLASSES = "manage_school_classes"
    INVITE_TEACHERS = "invite_teachers"
    VIEW_SCHOOL_ANALYTICS = "view_school_analytics"
    MANAGE_SCHOOL_CURRICULUM = "manage_school_curriculum"

    # Platform Administration Permissions
    APPROVE_GLOBAL_CONTENT = "approve_global_content"
    MANAGE_ALL_SCHOOLS = "manage_all_schools"
    ACCESS_AUDIT_LOGS = "access_audit_logs"
    CONFIGURE_PLATFORM_SAFETY = "configure_platform_safety"


ROLE_PERMISSION_MAP: Dict[str, Set[Permission]] = {
    "student": {
        Permission.ACCESS_CURRICULUM,
        Permission.USE_AI_TUTOR,
        Permission.TAKE_ASSESSMENT,
        Permission.VIEW_OWN_PROGRESS,
    },
    "parent": {
        Permission.VIEW_CHILD_PROGRESS,
        Permission.MANAGE_CHILD_CONSENT,
        Permission.CONFIGURE_SAFETY_CONTROLS,
        Permission.ACCESS_CURRICULUM,
    },
    "teacher": {
        Permission.ACCESS_CURRICULUM,
        Permission.MANAGE_ASSIGNED_CLASSES,
        Permission.VIEW_CLASS_ANALYTICS,
        Permission.AUTHOR_CUSTOM_QUIZ,
        Permission.TRIGGER_AI_QUIZ_GEN,
        Permission.FLAG_CONTENT_SAFETY,
        Permission.USE_AI_TUTOR,
    },
    "school_admin": {
        Permission.ACCESS_CURRICULUM,
        Permission.MANAGE_SCHOOL_CLASSES,
        Permission.INVITE_TEACHERS,
        Permission.VIEW_SCHOOL_ANALYTICS,
        Permission.MANAGE_SCHOOL_CURRICULUM,
        Permission.AUTHOR_CUSTOM_QUIZ,
        Permission.TRIGGER_AI_QUIZ_GEN,
        Permission.FLAG_CONTENT_SAFETY,
    },
    "admin": {
        # School / Platform Administrator
        Permission.ACCESS_CURRICULUM,
        Permission.MANAGE_SCHOOL_CLASSES,
        Permission.INVITE_TEACHERS,
        Permission.VIEW_SCHOOL_ANALYTICS,
        Permission.MANAGE_SCHOOL_CURRICULUM,
        Permission.APPROVE_GLOBAL_CONTENT,
        Permission.ACCESS_AUDIT_LOGS,
    },
    "super_admin": {
        # Full Platform Super Admin
        *Permission
    }
}


class RolePermissionMatrix:
    """
    Evaluates whether a role possesses a specific permission.
    """

    @classmethod
    def get_permissions(cls, role: str) -> Set[Permission]:
        return ROLE_PERMISSION_MAP.get(role.lower(), set())

    @classmethod
    def has_permission(cls, role: str, permission: Permission) -> bool:
        user_role = role.lower() if role else ""
        if user_role == "super_admin":
            return True
        allowed_perms = ROLE_PERMISSION_MAP.get(user_role, set())
        return permission in allowed_perms
