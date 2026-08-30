"""
Centralized Student Age Calculation & Minor Age-Banding Policy.
Used across recommendations, AI safety filtering, parental consent gating, and content cataloging.
"""

from typing import Optional, Dict, Any
import datetime
from app.models.models import StudentProfile

class StudentAgePolicy:
    MIN_STUDENT_AGE = 10
    MAX_STUDENT_AGE = 19
    GUARDIAN_CONSENT_AGE_THRESHOLD = 16  # Under 16 requires parental verification under DPDP/COPPA

    @staticmethod
    def calculate_age(date_of_birth: datetime.date) -> int:
        """Calculates precise calendar age taking month and day into account."""
        today = datetime.date.today()
        return (
            today.year
            - date_of_birth.year
            - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        )

    @classmethod
    def get_student_age(cls, profile: Optional[StudentProfile]) -> int:
        """
        Determines the student's operational target age.
        Prioritizes verified date of birth; derives from grade level (grade + 5) if DOB is pending.
        Defaults to 15 if no profile exists.
        """
        if not profile:
            return 15

        if profile.date_of_birth:
            return cls.calculate_age(profile.date_of_birth)

        if profile.school_class and profile.school_class.grade_level:
            return max(cls.MIN_STUDENT_AGE, min(cls.MAX_STUDENT_AGE, profile.school_class.grade_level + 5))

        if profile.grade_level:
            return max(cls.MIN_STUDENT_AGE, min(cls.MAX_STUDENT_AGE, profile.grade_level + 5))

        return 15

    @staticmethod
    def get_age_band(age: int) -> str:
        """Returns the appropriate pedagogical age band."""
        if age <= 12:
            return "BAND_10_12" # Middle School (Grades 6–7)
        elif age <= 15:
            return "BAND_13_15" # Secondary (Grades 8–10)
        else:
            return "BAND_16_18" # Senior Secondary (Grades 11–12)

    @staticmethod
    def get_allowed_content_policy(age: int) -> Dict[str, Any]:
        """Returns the permitted content difficulty and strictness policy by age."""
        if age <= 12:
            return {
                "max_difficulty": "medium",
                "min_safety_score": 90,
                "allow_external_embeds": False,
                "language_complexity": "simple",
                "recommended_duration_max": 15
            }
        elif age <= 15:
            return {
                "max_difficulty": "hard",
                "min_safety_score": 80,
                "allow_external_embeds": True,
                "language_complexity": "standard",
                "recommended_duration_max": 30
            }
        else:
            return {
                "max_difficulty": "hard",
                "min_safety_score": 75,
                "allow_external_embeds": True,
                "language_complexity": "advanced",
                "recommended_duration_max": 45
            }

    @staticmethod
    def get_ai_policy(age: int) -> Dict[str, Any]:
        """Returns AI Socratic guidance parameters and capability constraints by age."""
        if age <= 12:
            return {
                "socratic_depth": "guided_step_by_step",
                "max_response_length": 150,
                "tone": "encouraging_simple",
                "allow_code_generation": False,
                "strict_safety_gate": True
            }
        elif age <= 15:
            return {
                "socratic_depth": "inquiry_and_hints",
                "max_response_length": 250,
                "tone": "curriculum_coach",
                "allow_code_generation": True,
                "strict_safety_gate": True
            }
        else:
            return {
                "socratic_depth": "first_principles_deep_dive",
                "max_response_length": 400,
                "tone": "academic_rigorous",
                "allow_code_generation": True,
                "strict_safety_gate": True
            }

    @classmethod
    def is_minor(cls, age: int) -> bool:
        """Determines if student is under 18."""
        return age < 18

    @classmethod
    def requires_parental_consent(cls, age: int) -> bool:
        """Determines if student requires verifiable guardian consent."""
        return age < cls.GUARDIAN_CONSENT_AGE_THRESHOLD

AgePolicyService = StudentAgePolicy
age_policy = StudentAgePolicy()
