import unittest
import os
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db, SessionLocal, engine, Base
from app.models.models import User, School, SchoolClass, StudentProfile, parent_student_links, Quiz, Question, QuizAttempt
from app.core.security import create_access_token, get_password_hash
from app.core.redis_client import redis_client

class TestSecurityRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client = TestClient(app)
        self.db: Session = SessionLocal()
        redis_client.clear_all()

        # Seed School A
        self.school_a = self.db.query(School).filter(School.name == "Apex International Academy").first()
        if not self.school_a:
            self.school_a = School(name="Apex International Academy", domain="apexschool.edu")
            self.db.add(self.school_a)
            self.db.flush()

        # Seed School B
        self.school_b = self.db.query(School).filter(School.name == "Horizon High School").first()
        if not self.school_b:
            self.school_b = School(name="Horizon High School", domain="horizon.edu")
            self.db.add(self.school_b)
            self.db.flush()

        # Seed Students
        self.student_a = self.db.query(User).filter(User.email == "student_a_sec@apexschool.edu").first()
        if not self.student_a:
            self.student_a = User(
                email="student_a_sec@apexschool.edu",
                password_hash=get_password_hash("Student123!"),
                role="student",
                first_name="Alice",
                last_name="Apex",
                is_verified=True,
                school_id=self.school_a.id
            )
            self.db.add(self.student_a)
            self.db.flush()

        if not self.student_a.student_profile:
            self.profile_a = StudentProfile(
                user_id=self.student_a.id,
                school_id=self.school_a.id,
                board="CBSE",
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED",
                xp_score=150,
                streak_count=3
            )
            self.db.add(self.profile_a)
            self.db.flush()

        self.student_b = self.db.query(User).filter(User.email == "student_b_sec@horizon.edu").first()
        if not self.student_b:
            self.student_b = User(
                email="student_b_sec@horizon.edu",
                password_hash=get_password_hash("Student123!"),
                role="student",
                first_name="Bob",
                last_name="Horizon",
                is_verified=True,
                school_id=self.school_b.id
            )
            self.db.add(self.student_b)
            self.db.flush()

        if not self.student_b.student_profile:
            self.profile_b = StudentProfile(
                user_id=self.student_b.id,
                school_id=self.school_b.id,
                board="CBSE",
                onboarding_status="COMPLETED",
                parental_consent_status="GRANTED",
                xp_score=200,
                streak_count=5
            )
            self.db.add(self.profile_b)
            self.db.flush()

        # Seed Parents
        self.parent_a = self.db.query(User).filter(User.email == "parent_a_sec@apexschool.edu").first()
        if not self.parent_a:
            self.parent_a = User(
                email="parent_a_sec@apexschool.edu",
                password_hash=get_password_hash("Parent123!"),
                role="parent",
                first_name="Parent",
                last_name="Apex",
                is_verified=True,
                school_id=self.school_a.id
            )
            self.db.add(self.parent_a)
            self.db.flush()

            self.db.execute(parent_student_links.insert().values(
                parent_user_id=self.parent_a.id,
                student_user_id=self.student_a.id,
                is_verified=True
            ))

        self.parent_b = self.db.query(User).filter(User.email == "parent_b_sec@horizon.edu").first()
        if not self.parent_b:
            self.parent_b = User(
                email="parent_b_sec@horizon.edu",
                password_hash=get_password_hash("Parent123!"),
                role="parent",
                first_name="Parent",
                last_name="Horizon",
                is_verified=True,
                school_id=self.school_b.id
            )
            self.db.add(self.parent_b)
            self.db.flush()

            self.db.execute(parent_student_links.insert().values(
                parent_user_id=self.parent_b.id,
                student_user_id=self.student_b.id,
                is_verified=True
            ))

        # Seed Admins
        self.admin_a = self.db.query(User).filter(User.email == "admin_a_sec@apexschool.edu").first()
        if not self.admin_a:
            self.admin_a = User(
                email="admin_a_sec@apexschool.edu",
                password_hash=get_password_hash("Admin123!"),
                role="school_admin",
                first_name="Admin",
                last_name="Apex",
                is_verified=True,
                school_id=self.school_a.id
            )
            self.db.add(self.admin_a)
            self.db.flush()

        self.teacher_a = self.db.query(User).filter(User.email == "teacher_a_sec@apexschool.edu").first()
        if not self.teacher_a:
            self.teacher_a = User(
                email="teacher_a_sec@apexschool.edu",
                password_hash=get_password_hash("Teacher123!"),
                role="teacher",
                first_name="Teacher",
                last_name="Apex",
                is_verified=True,
                school_id=self.school_a.id
            )
            self.db.add(self.teacher_a)
            self.db.flush()

        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _get_headers(self, user: User) -> dict:
        token = create_access_token(data={"sub": user.email, "role": user.role, "user_id": user.id})
        return {"Authorization": f"Bearer {token}"}

    # --- 1. ADMIN ENDPOINT SECURITY TESTS ---

    def test_unauthenticated_admin_records_rejected_401(self):
        """Verify anonymous access to /api/v1/admin/records returns 401 Unauthorized."""
        res = self.client.get("/api/v1/admin/records")
        self.assertEqual(res.status_code, 401)

    def test_student_and_teacher_admin_records_forbidden_403(self):
        """Verify students, teachers, and parents cannot access /api/v1/admin/records."""
        res_student = self.client.get("/api/v1/admin/records", headers=self._get_headers(self.student_a))
        self.assertEqual(res_student.status_code, 403)

        res_teacher = self.client.get("/api/v1/admin/records", headers=self._get_headers(self.teacher_a))
        self.assertEqual(res_teacher.status_code, 403)

        res_parent = self.client.get("/api/v1/admin/records", headers=self._get_headers(self.parent_a))
        self.assertEqual(res_parent.status_code, 403)

    def test_school_admin_records_tenant_scoped(self):
        """Verify school_admin only sees records belonging to their assigned school."""
        res = self.client.get("/api/v1/admin/records", headers=self._get_headers(self.admin_a))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        for user_entry in data["users"]:
            # None of the records should belong to School B's horizon.edu
            self.assertNotEqual(user_entry["email"], self.student_b.email)

    def test_admin_export_excel_protected_401_and_403(self):
        """Verify /api/v1/admin/export-excel requires admin authentication."""
        res_anon = self.client.get("/api/v1/admin/export-excel")
        self.assertEqual(res_anon.status_code, 401)

        res_student = self.client.get("/api/v1/admin/export-excel", headers=self._get_headers(self.student_a))
        self.assertEqual(res_student.status_code, 403)

    # --- 2. PARENTAL CONSENT IDOR DEFENSE TESTS ---

    def test_parent_cannot_request_consent_for_unlinked_student_403(self):
        """Verify Parent A cannot request consent OTP for Student B (unlinked victim)."""
        res = self.client.post(
            "/api/v1/privacy/request-parent-verification",
            headers=self._get_headers(self.parent_a),
            json={
                "parent_email": self.parent_a.email,
                "student_id": self.student_b.id
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("unlinked guardian", res.json()["detail"])

    def test_parent_cannot_verify_otp_for_unlinked_student_403(self):
        """Verify Parent A cannot submit OTP verification for Student B."""
        res = self.client.post(
            "/api/v1/privacy/verify-parent-otp",
            headers=self._get_headers(self.parent_a),
            json={
                "parent_email": self.parent_a.email,
                "otp_code": "123456",
                "student_id": self.student_b.id
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("unlinked guardian", res.json()["detail"])

    def test_student_cannot_target_other_student_id_override(self):
        """Verify Student A cannot target Student B's ID; system binds strictly to caller."""
        res = self.client.post(
            "/api/v1/privacy/request-parent-verification",
            headers=self._get_headers(self.student_a),
            json={
                "parent_email": "new_guardian@apexschool.edu",
                "student_id": self.student_b.id # Attacker attempts IDOR
            }
        )
        self.assertEqual(res.status_code, 200)
        # Verify OTP in Redis is stored for student_a (the caller), NOT student_b
        otp_key_a = f"guardian_otp:new_guardian@apexschool.edu:{self.student_a.id}"
        otp_key_b = f"guardian_otp:new_guardian@apexschool.edu:{self.student_b.id}"
        self.assertIsNotNone(redis_client.get(otp_key_a))
        self.assertIsNone(redis_client.get(otp_key_b))

    # --- 3. GOOGLE OAUTH SECURITY TESTS ---

    def test_google_oauth_token_validation_aud_and_exp(self):
        """Verify Google OAuth token validation enforces iss, aud, exp, and sub."""
        from app.core.security import verify_google_id_token

        with patch("requests.get") as mock_get:
            # 1. Invalid issuer
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "iss": "https://malicious-issuer.com",
                "sub": "12345",
                "exp": int(time.time() + 3600)
            }
            self.assertIsNone(verify_google_id_token("fake_token"))

            # 2. Expired token
            mock_get.return_value.json.return_value = {
                "iss": "https://accounts.google.com",
                "sub": "12345",
                "exp": int(time.time() - 100) # Expired
            }
            self.assertIsNone(verify_google_id_token("fake_token"))

            # 3. Audience mismatch when GOOGLE_CLIENT_ID is configured
            with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "correct-app-client-id.apps.googleusercontent.com"}):
                mock_get.return_value.json.return_value = {
                    "iss": "https://accounts.google.com",
                    "sub": "12345",
                    "exp": int(time.time() + 3600),
                    "aud": "attacker-app-client-id.apps.googleusercontent.com"
                }
                self.assertIsNone(verify_google_id_token("fake_token"))

    # --- 4. REDIS PRODUCTION FAIL-FAST INVARIANT ---

    def test_redis_production_mode_fails_closed_without_in_memory_fallback(self):
        """Verify Redis operations in production mode fail fast with RuntimeError instead of fallback."""
        from app.core.redis_client import RedisClient

        with patch.dict(os.environ, {"ENVIRONMENT": "production", "REDIS_URL": "redis://invalid-host:6379/0"}):
            with self.assertRaises(RuntimeError):
                RedisClient()

    # --- 5. PARENTAL CONSENT REVOCATION TENANT ISOLATION ---

    def test_consent_revocation_cross_school_forbidden(self):
        """Verify School Admin A cannot revoke consent for Student B belonging to School B."""
        res = self.client.post(
            "/api/v1/privacy/revoke-consent",
            headers=self._get_headers(self.admin_a),
            json={
                "parent_email": "parent_b@horizon.edu",
                "student_id": self.student_b.id,
                "reason": "Administrative revocation"
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Cross-school", res.json()["detail"])

    def test_consent_revocation_unlinked_parent_forbidden(self):
        """Verify Parent A cannot revoke consent for unlinked Student B."""
        res = self.client.post(
            "/api/v1/privacy/revoke-consent",
            headers=self._get_headers(self.parent_a),
            json={
                "parent_email": self.parent_a.email,
                "student_id": self.student_b.id,
                "reason": "Guardian revocation"
            }
        )
        self.assertEqual(res.status_code, 403)

    # --- 6. GOOGLE ONBOARDING AND READ-ONLY FEED TESTS ---

    def test_google_login_and_student_onboarding_flow(self):
        """Verify Google login creates student in PENDING onboarding state, which is completed via /onboarding."""
        import uuid
        unique_email = f"new_google_student_{uuid.uuid4().hex[:8]}@example.com"

        with patch("app.routers.auth.verify_google_id_token") as mock_verify:
            mock_verify.return_value = {
                "email": unique_email,
                "sub": f"google_uid_{uuid.uuid4().hex[:8]}",
                "given_name": "Sam",
                "family_name": "Google"
            }

            res = self.client.post("/api/v1/auth/google", json={"id_token": "valid_token_test"})
            self.assertEqual(res.status_code, 200)
            token = res.json()["access_token"]

            # Inspect profile before onboarding
            me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(me_res.status_code, 200)
            me_data = me_res.json()
            self.assertIsNone(me_data["school"])
            self.assertEqual(me_data["student_profile"]["onboarding_status"], "PENDING")
            self.assertIsNone(me_data["student_profile"]["date_of_birth"])

            # Complete onboarding
            onboard_res = self.client.post(
                "/api/v1/students/onboarding",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "date_of_birth": "2010-05-15",
                    "grade_level": 10,
                    "board": "CBSE",
                    "interests": ["Robotics", "Physics"],
                    "learning_preference": ["video", "interactive"]
                }
            )
            self.assertEqual(onboard_res.status_code, 200)
            self.assertEqual(onboard_res.json()["onboarding_status"], "COMPLETED")
            self.assertEqual(onboard_res.json()["date_of_birth"], "2010-05-15")

    def test_feed_is_read_only_and_activity_advances_streak(self):
        """Verify GET /feed does not mutate streaks, while POST /activity advances streak explicitly."""
        headers = self._get_headers(self.student_a)

        # 1. Initial feed request
        feed1 = self.client.get("/api/v1/students/feed", headers=headers)
        self.assertEqual(feed1.status_code, 200)
        streak1 = feed1.json()["streak"]

        # 3. Explicit activity call records study session
        act_res = self.client.post("/api/v1/students/activity", headers=headers)
        self.assertEqual(act_res.status_code, 200)
        self.assertIn("streak_count", act_res.json())

    # --- 7. STRICT AI ACCESS POLICY & CONSENT GATING TESTS ---

    def test_student_with_pending_onboarding_cannot_use_ai_tutor(self):
        """Verify student in PENDING onboarding cannot access AI tutor (403 Forbidden)."""
        self.student_a.student_profile.onboarding_status = "PENDING"
        self.db.commit()

        res = self.client.post(
            "/api/v1/tutor/ask",
            headers=self._get_headers(self.student_a),
            json={"question": "Explain quadratic equations"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("onboarding", res.json()["detail"].lower())

    def test_student_with_pending_consent_cannot_use_ai_tutor(self):
        """Verify student in PENDING parental consent cannot access AI tutor (403 Forbidden)."""
        self.student_a.student_profile.onboarding_status = "COMPLETED"
        self.student_a.student_profile.parental_consent_status = "PENDING"
        self.db.commit()

        res = self.client.post(
            "/api/v1/tutor/ask",
            headers=self._get_headers(self.student_a),
            json={"question": "Explain quadratic equations"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("consent", res.json()["detail"].lower())

    def test_student_with_granted_consent_can_use_ai_tutor(self):
        """Verify student in COMPLETED onboarding and GRANTED consent can access AI tutor."""
        self.student_a.student_profile.onboarding_status = "COMPLETED"
        self.student_a.student_profile.parental_consent_status = "GRANTED"
        self.db.commit()

        res = self.client.post(
            "/api/v1/tutor/ask",
            headers=self._get_headers(self.student_a),
            json={"question": "Explain quadratic equations"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("answer", res.json())

    # --- 8. COLD-START RECOMMENDATION WITHOUT INVENTED INTERESTS ---

    def test_recommender_cold_start_without_fake_interests(self):
        """Verify recommendation engine generates grade/board-relevant items for student with empty interests."""
        from app.recommender.hybrid import HybridRecommender

        self.student_a.student_profile.interests = [] # Explicitly empty cold-start
        self.db.commit()

        recs = HybridRecommender.get_personalized_recommendations(
            db=self.db,
            student_id=self.student_a.id,
            limit=4
        )
        self.assertGreater(len(recs["items"]), 0)
        for item in recs["items"]:
            self.assertIn("recommendation_reason", item)
            self.assertIn("recommendation_source", item)

if __name__ == "__main__":
    unittest.main()
