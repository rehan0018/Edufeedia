"""
Centralized Student Age Calculation, Pedagogical Age-Banding, and DPDP Act 2023 Child Consent Policy.
Used across recommendations, AI safety filtering, parental consent gating, and content cataloging.
"""

from typing import Optional, Dict, Any, List
import datetime
from app.models.models import StudentProfile


class AgeBandPolicy:
    """
    Pedagogical and developmental age-banding policy for secondary school students (Grades 6–12 / Ages 10–17).
    """
    MIN_STUDENT_AGE = 10
    MAX_STUDENT_AGE = 17

    @staticmethod
    def calculate_age(date_of_birth: datetime.date) -> int:
        """Calculates precise calendar age taking month and day into account."""
        today = datetime.date.today()
        return (
            today.year
            - date_of_birth.year
            - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        )

    @staticmethod
    def get_age_band(age: int) -> str:
        """Returns the appropriate pedagogical age band."""
        if age <= 12:
            return "BAND_10_12"  # Middle School (Grades 6–7)
        elif age <= 15:
            return "BAND_13_15"  # Secondary (Grades 8–10)
        else:
            return "BAND_16_17"  # Senior Secondary (Grades 11–12)


class ChildConsentPolicy:
    """
    Statutory Child Protection & Verifiable Consent Engine.
    Enforces DPDP Act 2023 (Section 9) and COPPA standards: Any individual under 18 years is legally a child.
    """
    DPDP_CHILD_AGE_THRESHOLD = 18

    @classmethod
    def is_child(cls, age: int) -> bool:
        """Under DPDP Act Section 9, a child is an individual who has not completed 18 years of age."""
        return age < cls.DPDP_CHILD_AGE_THRESHOLD

    @classmethod
    def evaluate_consent_requirement(
        cls,
        age: int,
        processing_purpose: str = "ai_socratic_tutor",
        is_school_enrolled: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates verifiable parental consent obligations under DPDP Act 2023 & COPPA.
        """
        child_status = cls.is_child(age)
        requires_guardian_consent = child_status

        return {
            "is_child": child_status,
            "age": age,
            "requires_guardian_consent": requires_guardian_consent,
            "statutory_basis": "DPDP_Act_2023_Section_9",
            "consent_version": "2026.2-DPDP-COPPA",
            "processing_purpose": processing_purpose,
            "mandatory_scopes": [
                "ai_socratic_tutoring",
                "personalized_curriculum_recommendations",
                "formative_progress_and_mastery_tracking"
            ],
            "prohibited_activities": [
                "behavioral_monitoring_for_targeted_advertising",
                "unvetted_cross_tenant_data_sharing",
                "unsupervised_web_embed_tracking"
            ]
        }


class StudentAgePolicy:
    """
    Unified Façade for Student Age Evaluation, Safety Thresholds, and Content Policies.
    """
    MIN_STUDENT_AGE = AgeBandPolicy.MIN_STUDENT_AGE
    MAX_STUDENT_AGE = AgeBandPolicy.MAX_STUDENT_AGE
    GUARDIAN_CONSENT_AGE_THRESHOLD = ChildConsentPolicy.DPDP_CHILD_AGE_THRESHOLD

    @staticmethod
    def calculate_age(date_of_birth: datetime.date) -> int:
        return AgeBandPolicy.calculate_age(date_of_birth)

    @classmethod
    def validate_student_age(cls, dob: datetime.date) -> Dict[str, Any]:
        """Evaluates whether a student's age fits platform eligibility (10 to 17 / under 18)."""
        age = cls.calculate_age(dob)
        if age < cls.MIN_STUDENT_AGE or age > cls.MAX_STUDENT_AGE:
            return {
                "is_eligible": False,
                "age": age,
                "reason": f"Student age {age} not supported. Edufeedia is designed specifically for students aged {cls.MIN_STUDENT_AGE} to {cls.MAX_STUDENT_AGE}."
            }

        consent_eval = ChildConsentPolicy.evaluate_consent_requirement(age)
        return {
            "is_eligible": True,
            "age": age,
            "requires_guardian_consent": consent_eval["requires_guardian_consent"],
            "consent_evaluation": consent_eval,
            "consent_version": consent_eval["consent_version"]
        }

    @classmethod
    def get_student_age(cls, profile: Optional[StudentProfile]) -> int:
        """
        Determines the student's operational target age.
        Prioritizes verified date of birth; derives from grade level (grade + 5) if DOB is pending.
        Defaults to MIN_STUDENT_AGE (10) for maximum safety if no profile exists.
        """
        if not profile:
            return cls.MIN_STUDENT_AGE

        if profile.date_of_birth:
            return cls.calculate_age(profile.date_of_birth)

        if profile.school_class and profile.school_class.grade_level:
            return max(cls.MIN_STUDENT_AGE, min(cls.MAX_STUDENT_AGE, profile.school_class.grade_level + 5))

        if profile.grade_level:
            return max(cls.MIN_STUDENT_AGE, min(cls.MAX_STUDENT_AGE, profile.grade_level + 5))

        return cls.MIN_STUDENT_AGE

    @staticmethod
    def get_age_band(age: int) -> str:
        return AgeBandPolicy.get_age_band(age)

    @staticmethod
    def get_allowed_content_policy(age: int) -> Dict[str, Any]:
        """Returns the permitted content difficulty and single-source-of-truth safety score thresholds by age."""
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
        return ChildConsentPolicy.is_child(age)

    @classmethod
    def requires_parental_consent(cls, age: int) -> bool:
        return ChildConsentPolicy.is_child(age)

AgePolicyService = StudentAgePolicy
age_policy = StudentAgePolicy()
