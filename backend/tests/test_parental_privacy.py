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
        # 1. Post verifiable parental consent update
        res = client.post(
            "/api/v1/privacy/parental-consent",
            headers=self.parent_headers,
            json={
                "parent_email": "parent@gmail.com",
                "consent_granted": True,
                "verification_method": "email_otp_verified"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["consent_granted"])
        self.assertIn("consent_log_id", data)

        # 2. Verify audit record in database
        log_entry = self.db.query(ParentalConsentLog).filter(
            ParentalConsentLog.id == data["consent_log_id"]
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.consent_status, "granted")
        self.assertEqual(log_entry.verification_method, "email_otp_verified")
        self.assertIn("curriculum_access", log_entry.consent_scope)

    def test_parental_consent_revocation(self):
        # Revoke consent
        res = client.post(
            "/api/v1/privacy/parental-consent",
            headers=self.parent_headers,
            json={
                "parent_email": "parent@gmail.com",
                "consent_granted": False,
                "verification_method": "parent_portal_revocation"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["consent_granted"])

        # Check database log
        log_entry = self.db.query(ParentalConsentLog).filter(
            ParentalConsentLog.id == data["consent_log_id"]
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.consent_status, "revoked")
        self.assertIsNotNone(log_entry.revoked_at)

if __name__ == "__main__":
    unittest.main()
