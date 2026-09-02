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


from enum import Enum

class ProcessingPurpose(str, Enum):
    AI_SOCRATIC_TUTOR = "ai_socratic_tutor"
    PERSONALIZED_RECOMMENDATIONS = "personalized_recommendations"
    FORMATIVE_PROGRESS_TRACKING = "formative_progress_tracking"
    SAFETY_MONITORING = "safety_monitoring"
    SCHOOL_ADMINISTRATION = "school_administration"
    BILLING_AND_ACCOUNT = "billing_and_account"
    ANALYTICS_AGGREGATION = "analytics_aggregation"


class ChildConsentPolicy:
    """
    Statutory Child Protection & Purpose-Specific Verifiable Consent Engine.
    Enforces Edufeedia platform child protection policies (students aged 10–17) and DPDP Act 2023 Section 9
    statutory child definition (individuals under 18 years).
    Jurisdiction-specific legal obligations (e.g. DPDP Act 2023 Section 9 for India; COPPA/FERPA for US deployments)
    are mapped to purpose-specific legal bases.
    Institutional processing (e.g. School Administration) remains subject to strict purpose limitation,
    data minimization, access control, and retention policies even where individual guardian consent is not the statutory mechanism.
    """
    DPDP_CHILD_AGE_THRESHOLD = 18

    # Purpose-to-Policy-Basis and Consent Mapping
    PURPOSE_RULES: Dict[str, Dict[str, Any]] = {
        ProcessingPurpose.AI_SOCRATIC_TUTOR.value: {
            "policy_basis": "EXPLICIT_VERIFIABLE_GUARDIAN_CONSENT",
            "requires_explicit_consent": True,
            "consent_scope": "ai_socratic_tutoring",
            "description": "Interactive AI tutoring and real-time conceptual guidance"
        },
        ProcessingPurpose.PERSONALIZED_RECOMMENDATIONS.value: {
            "policy_basis": "EXPLICIT_VERIFIABLE_GUARDIAN_CONSENT",
            "requires_explicit_consent": True,
            "consent_scope": "personalized_curriculum_recommendations",
            "description": "Algorithmic adaptation and personalized learning feed"
        },
        ProcessingPurpose.FORMATIVE_PROGRESS_TRACKING.value: {
            "policy_basis": "CORE_EDUCATIONAL_SERVICE",
            "requires_explicit_consent": True,
            "consent_scope": "formative_progress_and_mastery_tracking",
            "description": "Diagnostic mastery scoring, quiz assessments, and learning streaks"
        },
        ProcessingPurpose.SAFETY_MONITORING.value: {
            "policy_basis": "CHILD_SAFETY_PROTECTION",
            "requires_explicit_consent": False,
            "consent_scope": "child_safety_and_prompt_injection_monitoring",
            "description": "Automated harm prevention, prompt injection filtering, and threat detection"
        },
        ProcessingPurpose.SCHOOL_ADMINISTRATION.value: {
            "policy_basis": "EDUCATIONAL_INSTITUTION_PROVISION",
            "requires_explicit_consent": False,
            "consent_scope": "institutional_class_management",
            "description": "Roster management, school enrollment, and attendance records"
        },
        ProcessingPurpose.ANALYTICS_AGGREGATION.value: {
            "policy_basis": "ANONYMIZED_AGGREGATE_RESEARCH",
            "requires_explicit_consent": False,
            "consent_scope": "deidentified_pedagogical_analytics",
            "description": "Aggregated, non-PII curriculum effectiveness analysis"
        }
    }

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
        Evaluates verifiable parental consent obligations for a specific processing purpose under DPDP Act 2023.
        """
        child_status = cls.is_child(age)
        rule = cls.PURPOSE_RULES.get(
            processing_purpose,
            {
                "policy_basis": "EXPLICIT_VERIFIABLE_GUARDIAN_CONSENT",
                "requires_explicit_consent": True,
                "consent_scope": processing_purpose,
                "description": "General student data processing"
            }
        )

        requires_explicit = rule["requires_explicit_consent"]
        # School administration exemption applies only if student is actively school-enrolled
        if processing_purpose == ProcessingPurpose.SCHOOL_ADMINISTRATION.value and not is_school_enrolled:
            requires_explicit = True

        requires_guardian_consent = child_status and requires_explicit

        return {
            "is_child": child_status,
            "age": age,
            "is_school_enrolled": is_school_enrolled,
            "processing_purpose": processing_purpose,
            "policy_basis": rule["policy_basis"],
            "legal_basis": rule["policy_basis"],
            "requires_guardian_consent": requires_guardian_consent,
            "consent_scope": rule["consent_scope"],
            "statutory_basis": "DPDP_Act_2023_Section_9",
            "consent_version": "2026.2-DPDP",
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
