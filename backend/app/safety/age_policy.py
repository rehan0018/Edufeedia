"""
Age Policy & Student Compliance Engine.
Enforces age appropriateness rules and COPPA/DPDP parental consent checks for students under 18.
"""

from typing import Dict, Any, Optional
import datetime

class AgePolicy:
    """Enforces strict age and grade-level boundaries."""
    MIN_ALLOWED_AGE = 10
    MAX_ALLOWED_AGE = 19
    CONSENT_REQUIRED_AGE_THRESHOLD = 16  # DPDP Act (India) and COPPA require guardian verification under 16/18

    @classmethod
    def calculate_age(cls, dob: datetime.date) -> int:
        today = datetime.date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @classmethod
    def validate_student_age(cls, dob: datetime.date) -> Dict[str, Any]:
        """Evaluates whether a student's age fits platform eligibility."""
        age = cls.calculate_age(dob)
        if age < cls.MIN_ALLOWED_AGE or age > cls.MAX_ALLOWED_AGE:
            return {
                "is_eligible": False,
                "age": age,
                "reason": f"Edufeedia is restricted to students aged {cls.MIN_ALLOWED_AGE}–{cls.MAX_ALLOWED_AGE}."
            }
        
        requires_guardian_consent = (age < cls.CONSENT_REQUIRED_AGE_THRESHOLD)
        return {
            "is_eligible": True,
            "age": age,
            "requires_guardian_consent": requires_guardian_consent,
            "consent_version": "2026.1-DPDP-COPPA"
        }

    @classmethod
    def is_grade_appropriate(cls, content_grade: int, student_grade: int) -> bool:
        """Ensures curriculum content is within 2 grade levels of student's current enrollment."""
        return abs(content_grade - student_grade) <= 2

age_policy = AgePolicy()
