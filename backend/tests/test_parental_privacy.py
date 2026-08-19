import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.models import ParentalConsentLog

client = TestClient(app)

class TestParentalPrivacyAndConsent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Authenticate as parent
        p_res = client.post("/api/v1/auth/login", json={
            "email": "parent@gmail.com",
            "password": "Parent123!"
        })
        assert p_res.status_code == 200
        cls.parent_token = p_res.json()["access_token"]
        cls.parent_headers = {"Authorization": f"Bearer {cls.parent_token}"}

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_verifiable_parental_consent_grant_and_audit(self):
        from app.core.redis_client import redis_client
        # 1. Student requests OTP
        s_res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        student_headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

        req_res = client.post(
            "/api/v1/privacy/request-parent-verification",
            headers=student_headers,
            json={"parent_email": "parent@gmail.com"}
        )
        self.assertEqual(req_res.status_code, 200)

        # Retrieve generated OTP from Redis
        student_id = s_res.json()["user_id"]
        otp = redis_client.get(f"guardian_otp:parent@gmail.com:{student_id}")
        self.assertIsNotNone(otp)

        # 2. Verify OTP
        v_res = client.post(
            "/api/v1/privacy/verify-parent-otp",
            headers=student_headers,
            json={
                "parent_email": "parent@gmail.com",
                "otp_code": otp,
                "student_id": student_id,
                "consent_scope": ["curriculum_access", "ai_socratic_tutor", "analytics_tracking"]
            }
        )
        self.assertEqual(v_res.status_code, 200)
        data = v_res.json()
        self.assertEqual(data["status"], "verified")
        self.assertTrue(data["consent_granted"])
        self.assertIn("consent_log_id", data)

        # 3. Verify audit record in database
        log_entry = self.db.query(ParentalConsentLog).filter(
            ParentalConsentLog.id == data["consent_log_id"]
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.consent_status, "granted")
        self.assertEqual(log_entry.verification_method, "email_otp_verified")
        self.assertIn("curriculum_access", log_entry.consent_scope)

    def test_parental_consent_revocation(self):
        # 1. Revoke consent
        res = client.post(
            "/api/v1/privacy/revoke-consent",
            headers=self.parent_headers,
            json={
                "parent_email": "parent@gmail.com"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "revoked")
        self.assertFalse(data["consent_granted"])

        # 2. Check database log
        log_entry = self.db.query(ParentalConsentLog).filter(
            ParentalConsentLog.id == data["consent_log_id"]
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.consent_status, "revoked")
        self.assertIsNotNone(log_entry.revoked_at)

if __name__ == "__main__":
    unittest.main()
