import unittest
import os
import sys
import datetime
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure backend root in path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.models import (
    User, School, SchoolClass, StudentProfile, ContentItem, ContentReport,
    QuizAttempt, SpacedRepetitionSchedule, parent_student_links, teacher_classes,
    ParentalConsentLog
)
from app.core.security import create_access_token, get_password_hash

class TestEducationalFeatures(unittest.TestCase):
    """
    Tests new educational capabilities:
    1. Content Reporting (student report -> teacher moderation queue -> resolve/dismiss)
    2. Learning Health Score calculation
    3. Parent Weekly Summary generation
    4. Teacher Intervention Alerts
    """

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db: Session = SessionLocal()

        # School & Class
        cls.school = cls._get_or_create_school_cls("Edu Features Academy", "edufeat.edu")
        cls.school_class = cls._get_or_create_class_cls(cls.school.id, 10, "A")

        # Teacher
        cls.teacher = cls._get_or_create_user_cls("teacher_feat@edufeat.edu", "teacher", "Tara", "Teacher", cls.school.id)
        cls._assign_teacher_cls(cls.teacher.id, cls.school_class.id, "Mathematics")

        # Student
        cls.student = cls._get_or_create_user_cls("student_feat@edufeat.edu", "student", "Sam", "Student", cls.school.id)
        cls.profile = cls._get_or_create_profile_cls(cls.student.id, cls.school.id, cls.school_class.id)

        # Parent
        cls.parent = cls._get_or_create_user_cls("parent_feat@family.edu", "parent", "Pam", "Parent", cls.school.id)
        cls._link_parent_cls(cls.parent.id, cls.student.id, verified=True)

        # Content Item
        cls.lesson = cls._get_or_create_content_cls("Quadratic Formula Proof", "Mathematics", "Algebra", approved=True)

        cls.db.close()

    def setUp(self):
        self.client = TestClient(app)
        self.db: Session = SessionLocal()
        self.student = self.db.query(User).filter(User.email == "student_feat@edufeat.edu").first()
        self.teacher = self.db.query(User).filter(User.email == "teacher_feat@edufeat.edu").first()
        self.parent = self.db.query(User).filter(User.email == "parent_feat@family.edu").first()
        self.lesson = self.db.query(ContentItem).filter(ContentItem.title == "Quadratic Formula Proof").first()

    def tearDown(self):
        try:
            self.db.rollback()
            self.db.close()
        except Exception:
            pass

    def _get_headers(self, user: User) -> dict:
        token = create_access_token(data={"sub": user.email, "role": user.role})
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    def _get_or_create_school_cls(cls, name: str, domain: str) -> School:
        s = cls.db.query(School).filter((School.name == name) | (School.domain == domain)).first()
        if not s:
            s = School(name=name, domain=domain)
            cls.db.add(s)
            cls.db.commit()
            cls.db.refresh(s)
        return s

    @classmethod
    def _get_or_create_class_cls(cls, school_id: str, grade: int, section: str) -> SchoolClass:
        sc = cls.db.query(SchoolClass).filter(
            SchoolClass.school_id == school_id,
            SchoolClass.grade_level == grade,
            SchoolClass.section_name == section
        ).first()
        if not sc:
            sc = SchoolClass(school_id=school_id, grade_level=grade, section_name=section, academic_year="2026-2027")
            cls.db.add(sc)
            cls.db.commit()
            cls.db.refresh(sc)
        return sc

    @classmethod
    def _get_or_create_user_cls(cls, email: str, role: str, first_name: str, last_name: str, school_id: str) -> User:
        u = cls.db.query(User).filter(User.email == email).first()
        if not u:
            u = User(
                email=email,
                password_hash=get_password_hash("Password123!"),
                role=role,
                first_name=first_name,
                last_name=last_name,
                is_verified=True,
                school_id=school_id,
                account_status="ACTIVE"
            )
            cls.db.add(u)
            cls.db.commit()
            cls.db.refresh(u)
        return u

    @classmethod
    def _get_or_create_profile_cls(cls, user_id: str, school_id: str, class_id: str) -> StudentProfile:
        p = cls.db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if not p:
            p = StudentProfile(
                user_id=user_id,
                school_id=school_id,
                class_id=class_id,
                board="CBSE",
                date_of_birth=datetime.date(2010, 4, 10),
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED",
                xp_score=150,
                streak_count=4
            )
            cls.db.add(p)
            cls.db.commit()
            cls.db.refresh(p)
        return p

    @classmethod
    def _assign_teacher_cls(cls, teacher_id: str, class_id: str, subject: str):
        existing = cls.db.query(teacher_classes).filter(
            teacher_classes.c.teacher_user_id == teacher_id,
            teacher_classes.c.class_id == class_id
        ).first()
        if not existing:
            cls.db.execute(teacher_classes.insert().values(
                teacher_user_id=teacher_id,
                class_id=class_id,
                subject=subject
            ))
            cls.db.commit()

    @classmethod
    def _link_parent_cls(cls, parent_id: str, student_id: str, verified: bool = True):
        existing = cls.db.query(parent_student_links).filter(
            parent_student_links.c.parent_user_id == parent_id,
            parent_student_links.c.student_user_id == student_id
        ).first()
        if not existing:
            cls.db.execute(parent_student_links.insert().values(
                parent_user_id=parent_id,
                student_user_id=student_id,
                is_verified=verified
            ))
            cls.db.commit()

    @classmethod
    def _get_or_create_content_cls(cls, title: str, subject: str, topic: str, approved: bool = True) -> ContentItem:
        c = cls.db.query(ContentItem).filter(ContentItem.title == title).first()
        if not c:
            c = ContentItem(
                title=title,
                source_url=f"https://khanacademy.org/math/{uuid.uuid4().hex[:8]}",
                source_platform="KhanAcademy",
                board="CBSE",
                grade_level=10,
                duration_minutes=20,
                subject=subject,
                topic=topic,
                type="reading",
                is_approved=approved,
                safety_score=98,
                edu_score=95
            )
            cls.db.add(c)
            cls.db.commit()
            cls.db.refresh(c)
        return c

    # =========================================================================
    # 1. CONTENT REPORTING LIFECYCLE
    # =========================================================================

    def test_content_reporting_and_moderation_lifecycle(self):
        """Student submits content report -> teacher inspects moderation queue -> resolves report."""
        student_headers = self._get_headers(self.student)
        teacher_headers = self._get_headers(self.teacher)

        # 1. Student reports content
        report_res = self.client.post(
            "/api/v1/content/report",
            headers=student_headers,
            json={
                "content_item_id": self.lesson.id,
                "reason": "Not age appropriate",
                "details": "Explanation contains terminology beyond Grade 10 curriculum."
            }
        )
        self.assertEqual(report_res.status_code, 200)
        report_data = report_res.json()
        report_id = report_data["id"]
        self.assertEqual(report_data["reason"], "Not age appropriate")
        self.assertEqual(report_data["status"], "pending_review")

        # 2. Teacher retrieves moderation queue
        queue_res = self.client.get("/api/v1/teachers/moderation-queue", headers=teacher_headers)
        self.assertEqual(queue_res.status_code, 200)
        reports = queue_res.json()
        self.assertTrue(any(r["id"] == report_id for r in reports))

        # 3. Teacher resolves report
        mod_res = self.client.post(
            "/api/v1/teachers/moderate-report",
            headers=teacher_headers,
            json={
                "report_id": report_id,
                "status": "resolved",
                "action_taken": "Adjusted difficulty grade tag from 10 to 11."
            }
        )
        self.assertEqual(mod_res.status_code, 200)
        self.assertEqual(mod_res.json()["status"], "resolved")

    # =========================================================================
    # 2. LEARNING HEALTH SCORE CALCULATION
    # =========================================================================

    def test_learning_health_score_calculation(self):
        """Student requests learning health score and receives composite index with pedagogical insight."""
        res = self.client.get("/api/v1/students/analytics/learning-health", headers=self._get_headers(self.student))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("learning_health_score", data)
        self.assertGreaterEqual(data["learning_health_score"], 0)
        self.assertLessEqual(data["learning_health_score"], 100)
        self.assertIn("status_label", data)
        self.assertIn("summary_insight", data)

    # =========================================================================
    # 3. PARENT WEEKLY SUMMARY
    # =========================================================================

    def test_parent_weekly_summary_generation(self):
        """Parent requests weekly learning digest for verified student."""
        res = self.client.get(
            f"/api/v1/parents/student/{self.student.id}/weekly-summary",
            headers=self._get_headers(self.parent)
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["student_id"], self.student.id)
        self.assertIn("lessons_completed", data)
        self.assertIn("parent_insight", data)

    # =========================================================================
    # 4. TEACHER INTERVENTIONS ENGINE
    # =========================================================================

    def test_teacher_interventions_endpoint(self):
        """Teacher queries interventions and receives structured alerts for assigned classrooms."""
        res = self.client.get("/api/v1/teachers/interventions", headers=self._get_headers(self.teacher))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_interventions", data)
        self.assertIn("interventions", data)

if __name__ == "__main__":
    unittest.main()
