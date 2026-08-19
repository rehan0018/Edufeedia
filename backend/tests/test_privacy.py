import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestChildPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Authenticate as student Priya
        res = client.post("/api/v1/auth/login", json={
            "email": "priya@apexschool.edu",
            "password": "Student123!"
        })
        assert res.status_code == 200
        cls.student_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        # Authenticate as parent
        p_res = client.post("/api/v1/auth/login", json={
            "email": "parent@gmail.com",
            "password": "Parent123!"
        })
        assert p_res.status_code == 200
        cls.parent_headers = {"Authorization": f"Bearer {p_res.json()['access_token']}"}

    def test_privacy_consent_status(self):
        res = client.get("/api/v1/privacy/consent-status", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("consent_status", data)
        self.assertTrue(data["data_minimization_enforced"])
        self.assertTrue(data["targeted_advertising_blocked"])
        self.assertTrue(data["third_party_tracking_blocked"])

    def test_parental_consent_otp_and_revocation(self):
        from app.core.redis_client import redis_client
        # 1. Student requests guardian OTP
        res = client.post(
            "/api/v1/privacy/request-parent-verification",
            headers=self.student_headers,
            json={"parent_email": "parent@gmail.com"}
        )
        self.assertEqual(res.status_code, 200)

        # Get generated OTP from Redis
        login_student = client.get("/api/v1/privacy/consent-status", headers=self.student_headers).json()
        student_id = login_student["user_id"]
        otp = redis_client.get(f"guardian_otp:parent@gmail.com:{student_id}")
        self.assertIsNotNone(otp)

        # 2. Verify OTP
        v_res = client.post(
            "/api/v1/privacy/verify-parent-otp",
            headers=self.student_headers,
            json={
                "parent_email": "parent@gmail.com",
                "otp_code": otp,
                "student_id": student_id
            }
        )
        self.assertEqual(v_res.status_code, 200)
        self.assertEqual(v_res.json()["status"], "verified")

        # 3. Revoke consent
        r_res = client.post(
            "/api/v1/privacy/revoke-consent",
            headers=self.parent_headers,
            json={
                "parent_email": "parent@gmail.com",
                "student_id": student_id
            }
        )
        self.assertEqual(r_res.status_code, 200)
        self.assertEqual(r_res.json()["status"], "revoked")

    def test_export_student_data_portability(self):
        res = client.get("/api/v1/privacy/export-my-data", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("user_account", data)
        self.assertIn("export_metadata", data)
        self.assertEqual(data["user_account"]["email"], "priya@apexschool.edu")

if __name__ == "__main__":
    unittest.main()
