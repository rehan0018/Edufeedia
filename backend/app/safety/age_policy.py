"""
Age Policy & Student Compliance Engine.
Re-exports canonical StudentAgePolicy from app.core.age_policy to eliminate duplicate definitions.
"""

from app.core.age_policy import StudentAgePolicy

class AgePolicy(StudentAgePolicy):
    """Enforces strict age and grade-level boundaries (Grades 6–12 / Ages 10–17)."""

    @classmethod
    def is_grade_appropriate(cls, content_grade: int, student_grade: int) -> bool:
        """Ensures curriculum content is within 2 grade levels of student's current enrollment."""
        return abs(content_grade - student_grade) <= 2

age_policy = AgePolicy()
