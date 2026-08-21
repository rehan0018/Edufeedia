import unittest
import sys
import os
import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import engine, Base, SessionLocal
from app.models.models import (
    User, School, SchoolClass, StudentProfile, StudentProgress, Quiz, Question,
    QuizAttempt, ContentItem, parent_student_links, teacher_classes, ClassAssignment
)
from app.core.security import get_password_hash
from app.embeddings.embedder import embed_content

class TestMultiUserAndTenantIsolation(unittest.TestCase):
    """
    Rigorously validates the Multi-User Isolation Matrix and Anti-IDOR Protections:
    - User A -> User A data (200 OK)
    - User A -> User B data (403 Forbidden / filtered)
    - Parent A -> Child A (200 OK)
    - Parent A -> Child B (403 Forbidden)
    - Teacher A -> Class A (200 OK)
    - Teacher A -> Class B (403 Forbidden)
    - School Admin A -> School A (200 OK)
    - School Admin A -> School B (403 Forbidden)
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        Base.metadata.create_all(bind=engine)
        cls.db: Session = SessionLocal()

        # 1. Establish Two Completely Distinct Schools (Tenant A vs. Tenant B)
        cls.school_a = cls.db.query(School).filter(School.domain == "alpha_multi.edu").first()
        if not cls.school_a:
            cls.school_a = School(name="Alpha Multi School", domain="alpha_multi.edu")
            cls.db.add(cls.school_a)
            cls.db.flush()

        cls.school_b = cls.db.query(School).filter(School.domain == "beta_multi.edu").first()
        if not cls.school_b:
            cls.school_b = School(name="Beta Multi School", domain="beta_multi.edu")
            cls.db.add(cls.school_b)
            cls.db.flush()

        # Classes
        cls.class_a = cls.db.query(SchoolClass).filter(SchoolClass.school_id == cls.school_a.id, SchoolClass.section_name == "A").first()
        if not cls.class_a:
            cls.class_a = SchoolClass(school_id=cls.school_a.id, grade_level=10, section_name="A", academic_year="2026-2027")
            cls.db.add(cls.class_a)
            cls.db.flush()

        cls.class_b = cls.db.query(SchoolClass).filter(SchoolClass.school_id == cls.school_b.id, SchoolClass.section_name == "B").first()
        if not cls.class_b:
            cls.class_b = SchoolClass(school_id=cls.school_b.id, grade_level=10, section_name="B", academic_year="2026-2027")
            cls.db.add(cls.class_b)
            cls.db.flush()

        # 2. Content Item & Quiz Fixture
        cls.content_item = cls.db.query(ContentItem).filter(ContentItem.title == "Algebraic Quadratics Multi-User").first()
        if not cls.content_item:
            cls.content_item = ContentItem(
                title="Algebraic Quadratics Multi-User",
                description="Solving polynomial quadratics",
                source_url="https://youtube.com/embed/test_url",
                source_platform="YouTube Safe EDU",
                embed_code="<iframe src='https://youtube.com/embed/test_url'></iframe>",
                type="video",
                subject="Mathematics",
                topic="Quadratic Equations",
                grade_level=10,
                board="CBSE",
                duration_minutes=15,
                is_approved=True,
                embedding=embed_content("Algebraic Quadratics Multi-User", "Solving polynomial quadratics", "Mathematics", "Quadratic Equations", ["Math"])
            )
            cls.db.add(cls.content_item)
            cls.db.flush()

        cls.quiz = cls.db.query(Quiz).filter(Quiz.content_item_id == cls.content_item.id).first()
        if not cls.quiz:
            cls.quiz = Quiz(content_item_id=cls.content_item.id, title="Quadratics Multi-User Quiz")
            cls.db.add(cls.quiz)
            cls.db.flush()

            cls.q1 = Question(
                quiz_id=cls.quiz.id,
                question_text="Roots of x^2 - 4 = 0?",
                options=["x = ±2", "x = 4", "x = 0", "x = 1"],
                correct_answer="x = ±2",
                explanation="Difference of squares.",
                difficulty="easy"
            )
            cls.db.add(cls.q1)

        # 3. Two Distinct Students (Student A in School A, Student B in School B)
        cls.student_a = cls.db.query(User).filter(User.email == "alice_multi@alpha.edu").first()
        if not cls.student_a:
            cls.student_a = User(
                email="alice_multi@alpha.edu",
                password_hash=get_password_hash("StudentA123!"),
                role="student",
                first_name="Alice",
                last_name="Alpha",
                is_verified=True,
                identity_verified=True,
                account_status="ACTIVE",
                school_id=cls.school_a.id
            )
            cls.db.add(cls.student_a)
            cls.db.flush()

        cls.student_b = cls.db.query(User).filter(User.email == "bob_multi@beta.edu").first()
        if not cls.student_b:
            cls.student_b = User(
                email="bob_multi@beta.edu",
                password_hash=get_password_hash("StudentB123!"),
                role="student",
                first_name="Bob",
                last_name="Beta",
                is_verified=True,
                identity_verified=True,
                account_status="ACTIVE",
                school_id=cls.school_b.id
            )
            cls.db.add(cls.student_b)
            cls.db.flush()

        cls.profile_a = cls.db.query(StudentProfile).filter(StudentProfile.user_id == cls.student_a.id).first()
        if not cls.profile_a:
            cls.profile_a = StudentProfile(
                user_id=cls.student_a.id,
                school_id=cls.school_a.id,
                class_id=cls.class_a.id,
                board="CBSE",
                date_of_birth=datetime.date(2011, 4, 10),
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED",
                xp_score=150,
                streak_count=4,
                interests=["Mathematics"]
            )
            cls.db.add(cls.profile_a)

        cls.profile_b = cls.db.query(StudentProfile).filter(StudentProfile.user_id == cls.student_b.id).first()
        if not cls.profile_b:
            cls.profile_b = StudentProfile(
                user_id=cls.student_b.id,
                school_id=cls.school_b.id,
                class_id=cls.class_b.id,
                board="CBSE",
                date_of_birth=datetime.date(2011, 9, 20),
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED",
                xp_score=50,
                streak_count=1,
                interests=["Coding"]
            )
            cls.db.add(cls.profile_b)

        # 4. Parents (Parent A linked only to Student A)
        cls.parent_a = cls.db.query(User).filter(User.email == "parent_alice_multi@gmail.com").first()
        if not cls.parent_a:
            cls.parent_a = User(
                email="parent_alice_multi@gmail.com",
                password_hash=get_password_hash("ParentA123!"),
                role="parent",
                first_name="Mary",
                last_name="Alpha",
                is_verified=True
            )
            cls.db.add(cls.parent_a)
            cls.db.flush()

            cls.db.execute(parent_student_links.insert().values(
                parent_user_id=cls.parent_a.id,
                student_user_id=cls.student_a.id,
                is_verified=True
            ))

        # 5. Teachers (Teacher A assigned to School A Class A; Teacher B to School B Class B)
        cls.teacher_a = cls.db.query(User).filter(User.email == "teacher_alice_multi@alpha.edu").first()
        if not cls.teacher_a:
            cls.teacher_a = User(
                email="teacher_alice_multi@alpha.edu",
                password_hash=get_password_hash("TeacherA123!"),
                role="teacher",
                first_name="Teresa",
                last_name="Alpha",
                is_verified=True,
                school_id=cls.school_a.id
            )
            cls.db.add(cls.teacher_a)
            cls.db.flush()
            cls.db.execute(teacher_classes.insert().values(teacher_user_id=cls.teacher_a.id, class_id=cls.class_a.id, subject="Math"))

        cls.teacher_b = cls.db.query(User).filter(User.email == "teacher_bob_multi@beta.edu").first()
        if not cls.teacher_b:
            cls.teacher_b = User(
                email="teacher_bob_multi@beta.edu",
                password_hash=get_password_hash("TeacherB123!"),
                role="teacher",
                first_name="Thomas",
                last_name="Beta",
                is_verified=True,
                school_id=cls.school_b.id
            )
            cls.db.add(cls.teacher_b)
            cls.db.flush()
            cls.db.execute(teacher_classes.insert().values(teacher_user_id=cls.teacher_b.id, class_id=cls.class_b.id, subject="Coding"))

        # 6. School Admins (Admin A for School A; Admin B for School B)
        cls.admin_a = cls.db.query(User).filter(User.email == "admin_multi@alpha.edu").first()
        if not cls.admin_a:
            cls.admin_a = User(
                email="admin_multi@alpha.edu",
                password_hash=get_password_hash("AdminA123!"),
                role="school_admin",
                first_name="Arthur",
                last_name="Admin",
                is_verified=True,
                school_id=cls.school_a.id
            )
            cls.db.add(cls.admin_a)

        cls.admin_b = cls.db.query(User).filter(User.email == "admin_multi@beta.edu").first()
        if not cls.admin_b:
            cls.admin_b = User(
                email="admin_multi@beta.edu",
                password_hash=get_password_hash("AdminB123!"),
                role="school_admin",
                first_name="Beatrice",
                last_name="Admin",
                is_verified=True,
                school_id=cls.school_b.id
            )
            cls.db.add(cls.admin_b)

        # Super Admin
        cls.super_admin = cls.db.query(User).filter(User.email == "superadmin_multi@edufeedia.org").first()
        if not cls.super_admin:
            cls.super_admin = User(
                email="superadmin_multi@edufeedia.org",
                password_hash=get_password_hash("SuperAdmin123!"),
                role="admin",
                first_name="Platform",
                last_name="SuperAdmin",
                is_verified=True
            )
            cls.db.add(cls.super_admin)

        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        fresh_db = SessionLocal()
        try:
            fresh_db.query(StudentProgress).filter(
                StudentProgress.student_user_id.in_([self.student_a.id, self.student_b.id])
            ).delete(synchronize_session=False)
            fresh_db.query(QuizAttempt).filter(
                QuizAttempt.student_user_id.in_([self.student_a.id, self.student_b.id])
            ).delete(synchronize_session=False)
            fresh_db.commit()
        finally:
            fresh_db.close()

    def _login(self, email: str, password: str) -> dict:
        res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        self.assertEqual(res.status_code, 200, f"Login failed for {email}: {res.text}")
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # --- 1. STUDENT DATA SEPARATION & ANTI-IDOR TESTS ---

    def test_student_a_and_b_have_independent_dashboard_and_progress(self):
        headers_a = self._login("alice_multi@alpha.edu", "StudentA123!")
        headers_b = self._login("bob_multi@beta.edu", "StudentB123!")

        # Student A updates progress on math lesson
        prog_res = self.client.post("/api/v1/content/progress", headers=headers_a, json={
            "content_item_id": self.content_item.id,
            "progress_percentage": 100
        })
        self.assertEqual(prog_res.status_code, 200)

        # Student A dashboard shows lessons completed
        dash_a = self.client.get("/api/v1/students/dashboard", headers=headers_a).json()
        self.assertGreaterEqual(dash_a["total_lessons_completed"], 1)

        # Student B dashboard shows 0 lessons completed on this item
        dash_b = self.client.get("/api/v1/students/dashboard", headers=headers_b).json()
        self.assertEqual(dash_b["total_lessons_completed"], 0)

    def test_student_cannot_spoof_progress_as_another_user(self):
        """Even if malicious payload includes another student's ID, server strictly uses JWT."""
        headers_b = self._login("bob_multi@beta.edu", "StudentB123!")

        # Attempt to inject student_id in body
        res = self.client.post("/api/v1/content/progress", headers=headers_b, json={
            "student_id": self.student_a.id,
            "content_item_id": self.content_item.id,
            "progress_percentage": 100
        })
        self.assertEqual(res.status_code, 200)

        # Confirm progress was recorded for Bob (Student B), NOT Alice (Student A)
        fresh_db = SessionLocal()
        try:
            b_progress = fresh_db.query(StudentProgress).filter(
                StudentProgress.student_user_id == self.student_b.id,
                StudentProgress.content_item_id == self.content_item.id
            ).first()
            self.assertIsNotNone(b_progress)
        finally:
            fresh_db.close()

    # --- 2. PARENT-CHILD RELATIONAL ISOLATION TESTS ---

    def test_parent_a_can_access_own_linked_child_progress_only(self):
        headers_p = self._login("parent_alice_multi@gmail.com", "ParentA123!")

        # Parent A queries linked Alice (Student A) -> 200 OK
        res_a = self.client.get(f"/api/v1/parents/student/{self.student_a.id}/progress", headers=headers_p)
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json()["student_name"], "Alice Alpha")

    def test_parent_a_cannot_access_unlinked_child_progress(self):
        headers_p = self._login("parent_alice_multi@gmail.com", "ParentA123!")

        # Parent A queries unlinked Bob (Student B) -> 403 Forbidden
        res_b = self.client.get(f"/api/v1/parents/student/{self.student_b.id}/progress", headers=headers_p)
        self.assertEqual(res_b.status_code, 403)
        self.assertIn("authorized", res_b.json()["detail"].lower())

    # --- 3. TEACHER CLASS SCOPING & ASSIGNMENT ISOLATION TESTS ---

    def test_teacher_a_can_access_assigned_class_analytics(self):
        headers_t = self._login("teacher_alice_multi@alpha.edu", "TeacherA123!")

        # Teacher A accesses Class 10-A (assigned) -> 200 OK
        res = self.client.get(f"/api/v1/teachers/classes/{self.class_a.id}/analytics", headers=headers_t)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["class_id"], self.class_a.id)

    def test_teacher_a_cannot_access_foreign_class_analytics(self):
        headers_t = self._login("teacher_alice_multi@alpha.edu", "TeacherA123!")

        # Teacher A accesses Class 10-B (School B / unassigned) -> 403 Forbidden
        res = self.client.get(f"/api/v1/teachers/classes/{self.class_b.id}/analytics", headers=headers_t)
        self.assertEqual(res.status_code, 403)
        self.assertIn("denied", res.json()["detail"].lower())

    def test_teacher_cannot_create_assignment_for_unassigned_class(self):
        headers_t = self._login("teacher_alice_multi@alpha.edu", "TeacherA123!")

        # Teacher A attempts to assign homework to Class 10-B -> 403 Forbidden
        res = self.client.post("/api/v1/teachers/assignments", headers=headers_t, json={
            "class_id": self.class_b.id,
            "title": "Cross-School Injected Homework",
            "instructions": "Do problems 1 to 5",
            "due_date": str(datetime.date.today() + datetime.timedelta(days=2))
        })
        self.assertEqual(res.status_code, 403)

    # --- 4. SCHOOL ADMINISTRATOR TENANT ISOLATION TESTS ---

    def test_school_admin_records_are_scoped_strictly_to_own_school(self):
        headers_admin_a = self._login("admin_multi@alpha.edu", "AdminA123!")

        # Admin A fetches database records
        res = self.client.get("/api/v1/admin/records", headers=headers_admin_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Should contain School A students (Alice)
        student_emails = [s["email"] for s in data["students"]]
        self.assertIn("alice_multi@alpha.edu", student_emails)

        # Must NEVER contain School B students (Bob)
        self.assertNotIn("bob_multi@beta.edu", student_emails)

    def test_school_admin_cannot_invite_teacher_to_foreign_class(self):
        headers_admin_a = self._login("admin_multi@alpha.edu", "AdminA123!")

        # Admin A attempts to invite teacher and assign to School B's class
        res = self.client.post("/api/v1/admin/invite-teacher", headers=headers_admin_a, json={
            "email": "hacked_teacher_test@alpha.edu",
            "first_name": "Eve",
            "last_name": "Hacker",
            "class_ids": [self.class_b.id] # Class from School B
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("tenant", res.json()["detail"].lower())

    # --- 5. SUPER ADMIN PLATFORM AUDITING TESTS ---

    def test_super_admin_has_global_access(self):
        headers_super = self._login("superadmin_multi@edufeedia.org", "SuperAdmin123!")

        res = self.client.get("/api/v1/admin/records", headers=headers_super)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Super admin sees all students across School A and School B
        student_emails = [s["email"] for s in data["students"]]
        self.assertIn("alice_multi@alpha.edu", student_emails)
        self.assertIn("bob_multi@beta.edu", student_emails)

if __name__ == "__main__":
    unittest.main()
