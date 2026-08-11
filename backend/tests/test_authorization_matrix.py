import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestRoleAuthorizationMatrix(unittest.TestCase):
    """
    Validates Role-Based Access Control (RBAC) boundaries across student, parent, teacher, and admin roles.
    """

    @classmethod
    def setUpClass(cls):
        # 1. Student Token
        s_res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        assert s_res.status_code == 200
        cls.student_headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

        # 2. Parent Token
        p_res = client.post("/api/v1/auth/login", json={
            "email": "parent@gmail.com",
            "password": "Parent123!"
        })
        assert p_res.status_code == 200
        cls.parent_headers = {"Authorization": f"Bearer {p_res.json()['access_token']}"}

        # 3. Teacher Token
        t_res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        assert t_res.status_code == 200
        cls.teacher_headers = {"Authorization": f"Bearer {t_res.json()['access_token']}"}

    def test_unauthenticated_request_rejected(self):
        # Accessing protected feed without token returns 401
        res = client.get("/api/v1/recommendations/feed")
        self.assertEqual(res.status_code, 401)

    def test_student_cannot_access_ingestion_moderation_queue(self):
        # Students must receive 403 Forbidden on teacher ingestion endpoints
        res = client.get("/api/v1/content/ingestion/pending", headers=self.student_headers)
        self.assertEqual(res.status_code, 403)

    def test_student_cannot_generate_quizzes(self):
        # Students cannot trigger teacher quiz generation
        res = client.post(
            "/api/v1/quizzes/generate",
            headers=self.student_headers,
            json={"subject": "Mathematics", "topic": "Algebra", "grade_level": 10, "num_questions": 3}
        )
        self.assertEqual(res.status_code, 403)

    def test_parent_cannot_access_teacher_tools(self):
        # Parents cannot review staged content
        res = client.post(
            "/api/v1/content/ingestion/some_id/review",
            headers=self.parent_headers,
            json={"action": "approve"}
        )
        self.assertEqual(res.status_code, 403)

    def test_teacher_can_access_ingestion_queue(self):
        # Teachers have access to review queues
        res = client.get("/api/v1/content/ingestion/pending", headers=self.teacher_headers)
        self.assertEqual(res.status_code, 200)

    def test_health_and_readiness_are_public(self):
        # Probes are publicly accessible without authentication
        res_h = client.get("/health")
        self.assertEqual(res_h.status_code, 200)
        self.assertEqual(res_h.json()["status"], "healthy")

        res_r = client.get("/ready")
        self.assertEqual(res_r.status_code, 200)
        self.assertEqual(res_r.json()["status"], "ready")

if __name__ == "__main__":
    unittest.main()
