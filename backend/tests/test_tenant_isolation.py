import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.models import User, School, SchoolClass, StudentProfile, parent_student_links
from app.core.security import create_access_token, get_password_hash

class TestTenantIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client = TestClient(app)
        self.db: Session = SessionLocal()

        # Seed School Alpha
        self.school_alpha = self.db.query(School).filter((School.name == "Alpha Academy") | (School.domain == "alpha.edu")).first()
        if not self.school_alpha:
            self.school_alpha = School(name="Alpha Academy", domain="alpha.edu")
            self.db.add(self.school_alpha)
            self.db.flush()

        # Seed School Beta
        self.school_beta = self.db.query(School).filter((School.name == "Beta High") | (School.domain == "beta.edu")).first()
        if not self.school_beta:
            self.school_beta = School(name="Beta High", domain="beta.edu")
            self.db.add(self.school_beta)
            self.db.flush()

        # Seed Student Alpha
        self.student_alpha = self.db.query(User).filter(User.email == "student@alpha.edu").first()
        if not self.student_alpha:
            self.student_alpha = User(
                email="student@alpha.edu",
                password_hash=get_password_hash("Pass123!"),
                role="student",
                first_name="Alpha",
                last_name="Student",
                is_verified=True,
                school_id=self.school_alpha.id
            )
            self.db.add(self.student_alpha)
            self.db.flush()

        if not self.student_alpha.student_profile:
            self.profile_alpha = StudentProfile(
                user_id=self.student_alpha.id,
                school_id=self.school_alpha.id,
                board="CBSE",
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED"
            )
            self.db.add(self.profile_alpha)
            self.db.flush()

        # Seed Student Beta
        self.student_beta = self.db.query(User).filter(User.email == "student@beta.edu").first()
        if not self.student_beta:
            self.student_beta = User(
                email="student@beta.edu",
                password_hash=get_password_hash("Pass123!"),
                role="student",
                first_name="Beta",
                last_name="Student",
                is_verified=True,
                school_id=self.school_beta.id
            )
            self.db.add(self.student_beta)
            self.db.flush()

        if not self.student_beta.student_profile:
            self.profile_beta = StudentProfile(
                user_id=self.student_beta.id,
                school_id=self.school_beta.id,
                board="CBSE",
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED"
            )
            self.db.add(self.profile_beta)
            self.db.flush()

        # Seed Admin Alpha
        self.admin_alpha = self.db.query(User).filter(User.email == "admin@alpha.edu").first()
        if not self.admin_alpha:
            self.admin_alpha = User(
                email="admin@alpha.edu",
                password_hash=get_password_hash("Admin123!"),
                role="school_admin",
                first_name="Alpha",
                last_name="Admin",
                is_verified=True,
                school_id=self.school_alpha.id
            )
            self.db.add(self.admin_alpha)
            self.db.flush()

        # Seed Teacher Alpha
        self.teacher_alpha = self.db.query(User).filter(User.email == "teacher@alpha.edu").first()
        if not self.teacher_alpha:
            self.teacher_alpha = User(
                email="teacher@alpha.edu",
                password_hash=get_password_hash("Teacher123!"),
                role="teacher",
                first_name="Alpha",
                last_name="Teacher",
                is_verified=True,
                school_id=self.school_alpha.id
            )
            self.db.add(self.teacher_alpha)
            self.db.flush()

        # Seed Parent Alpha
        self.parent_alpha = self.db.query(User).filter(User.email == "parent@alpha.edu").first()
        if not self.parent_alpha:
            self.parent_alpha = User(
                email="parent@alpha.edu",
                password_hash=get_password_hash("Parent123!"),
                role="parent",
                first_name="Alpha",
                last_name="Parent",
                is_verified=True,
                school_id=self.school_alpha.id
            )
            self.db.add(self.parent_alpha)
            self.db.flush()

            self.db.execute(parent_student_links.insert().values(
                parent_user_id=self.parent_alpha.id,
                student_user_id=self.student_alpha.id,
                is_verified=True
            ))

        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _get_headers(self, user: User):
        token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
        return {"Authorization": f"Bearer {token}"}

    def test_cross_school_admin_access_forbidden(self):
        """School Admin Alpha cannot perform operations on Student Beta from School Beta."""
        res = self.client.post(
            "/api/v1/privacy/revoke-consent",
            headers=self._get_headers(self.admin_alpha),
            json={
                "parent_email": "guardian@beta.edu",
                "student_id": self.student_beta.id,
                "reason": "Administrative action"
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Cross-school", res.json()["detail"])

    def test_unlinked_parent_access_forbidden(self):
        """Parent Alpha cannot access or revoke consent for unlinked Student Beta."""
        res = self.client.post(
            "/api/v1/privacy/revoke-consent",
            headers=self._get_headers(self.parent_alpha),
            json={
                "parent_email": self.parent_alpha.email,
                "student_id": self.student_beta.id,
                "reason": "Guardian action"
            }
        )
        self.assertEqual(res.status_code, 403)

    def test_anonymous_and_student_forbidden_from_admin_endpoints(self):
        """Anonymous callers and students receive 401/403 when attempting admin access."""
        anon_res = self.client.get("/api/v1/admin/records")
        self.assertEqual(anon_res.status_code, 401)

        student_res = self.client.get("/api/v1/admin/records", headers=self._get_headers(self.student_alpha))
        self.assertEqual(student_res.status_code, 403)

if __name__ == "__main__":
    unittest.main()
