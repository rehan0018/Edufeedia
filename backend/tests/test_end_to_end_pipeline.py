import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.models import ContentItem, CurriculumChunk, IngestedSource

client = TestClient(app)

class TestEndToEndEdufeediaPipeline(unittest.TestCase):
    """
    End-to-End Integration Test validating the complete Edufeedia lifecycle:
    URL Ingestion → Adapter Fetch → SHA-256 Deduplication → Safety Audit →
    Teacher Approval → Vector & Chunk Staging → RAG Hybrid Retrieval → AI Tutor Response.
    """

    @classmethod
    def setUpClass(cls):
        # 1. Authenticate Teacher
        t_res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        assert t_res.status_code == 200
        cls.teacher_token = t_res.json()["access_token"]
        cls.teacher_headers = {"Authorization": f"Bearer {cls.teacher_token}"}

        # 2. Authenticate Student
        s_res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        assert s_res.status_code == 200
        cls.student_token = s_res.json()["access_token"]
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_complete_end_to_end_flow(self):
        # --- Stage 1: URL Ingestion Submission (Teacher) ---
        ingest_payload = {
            "url": "https://phet.colorado.edu/sims/html/projectile-motion/latest/projectile-motion_all.html",
            "title": "Projectile Motion and Quadratic Trajectories",
            "description": "Interactive physics simulation calculating parabolic trajectory, launch velocity, and gravitational acceleration.",
            "board": "CBSE",
            "content_type": "interactive"
        }
        res_submit = client.post(
            "/api/v1/content/ingestion/submit",
            headers=self.teacher_headers,
            json=ingest_payload
        )
        self.assertIn(res_submit.status_code, [200, 201])
        data_submit = res_submit.json()
        self.assertTrue(data_submit["success"])
        staged_id = data_submit.get("content_item_id") or data_submit.get("source_id")

        # --- Stage 2: Verify Pending Moderation Queue ---
        res_queue = client.get("/api/v1/content/ingestion/pending", headers=self.teacher_headers)
        self.assertEqual(res_queue.status_code, 200)

        # --- Stage 3: Teacher Review & Approval ---
        res_review = client.post(
            f"/api/v1/content/ingestion/{staged_id}/review",
            headers=self.teacher_headers,
            json={"action": "approve", "moderator_notes": "Verified CBSE Grade 10 Physics alignment."}
        )
        self.assertIn(res_review.status_code, [200, 201])

        # --- Stage 4: Verify ContentItem in Catalog ---
        fresh_db = SessionLocal()
        try:
            live_item = fresh_db.query(ContentItem).filter(ContentItem.id == staged_id).first()
            self.assertIsNotNone(live_item)
            self.assertTrue(live_item.is_approved)
            self.assertEqual(len(live_item.embedding), 384)
        finally:
            fresh_db.close()

        # --- Stage 5: Semantic Search Retrieval by Student ---
        res_search = client.get(
            "/api/v1/content/search?q=projectile parabolic trajectory gravity",
            headers=self.student_headers
        )
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertGreater(search_data["total_results"], 0)

        # --- Stage 6: Socratic AI Tutor Query by Student ---
        res_tutor = client.post(
            "/api/v1/tutor/ask",
            headers=self.student_headers,
            json={
                "question": "How does gravity affect the parabolic path of a projectile in motion?"
            }
        )
        self.assertEqual(res_tutor.status_code, 200)
        tutor_data = res_tutor.json()
        self.assertTrue(tutor_data["is_safe"])
        self.assertIn("answer", tutor_data)
        self.assertIn("socratic_cue", tutor_data)
        self.assertGreater(len(tutor_data["follow_up_questions"]), 0)

if __name__ == "__main__":
    unittest.main()
