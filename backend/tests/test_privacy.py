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

    def test_parental_consent_update(self):
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

    def test_export_student_data_portability(self):
        res = client.get("/api/v1/privacy/export-my-data", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("user_account", data)
        self.assertIn("export_metadata", data)
        self.assertEqual(data["user_account"]["email"], "priya@apexschool.edu")

if __name__ == "__main__":
    unittest.main()
