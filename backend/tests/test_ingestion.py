import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.ingestion.source_verifier import SourceVerifier
from app.ingestion.metadata_extractor import MetadataExtractor

client = TestClient(app)

class TestContentIngestion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Authenticate as teacher
        t_res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        assert t_res.status_code == 200
        cls.teacher_headers = {"Authorization": f"Bearer {t_res.json()['access_token']}"}

    def test_source_verifier_trusted_whitelist(self):
        # Trusted YouTube Safe EDU
        res = SourceVerifier.verify_url("https://www.youtube.com/watch?v=3nL2_O1wZ5Y")
        self.assertTrue(res["is_verified"])
        self.assertTrue(res["is_trusted_domain"])
        self.assertIn("youtube-nocookie.com/embed", res["embed_code"])

        # Trusted Khan Academy
        res_khan = SourceVerifier.verify_url("https://www.khanacademy.org/math/algebra/quadratics")
        self.assertTrue(res_khan["is_verified"])
        self.assertEqual(res_khan["platform"], "Khan Academy")

    def test_source_verifier_blocked_entertainment(self):
        # Social distraction platform
        res_tiktok = SourceVerifier.verify_url("https://www.tiktok.com/@funnyclips/video/12345")
        self.assertFalse(res_tiktok["is_verified"])
        self.assertFalse(res_tiktok["is_trusted_domain"])
        self.assertIn("blocked", res_tiktok["reason"].lower())

    def test_metadata_extractor_calculations(self):
        meta = MetadataExtractor.extract_metadata(
            title="Mastering Quadratic Equations: Roots & Discriminant",
            description="Explore quadratic formulas, calculating discriminant D = b^2 - 4ac, and step-by-step factorization.",
            raw_text="Quadratic equations form parabolic curves and help solve optimization problems."
        )
        self.assertEqual(meta["subject"], "Mathematics")
        self.assertEqual(meta["topic"], "Quadratic Equations")
        self.assertGreaterEqual(meta["estimated_grade"], 6)
        self.assertLessEqual(meta["estimated_grade"], 12)
        self.assertGreater(meta["edu_score"], 60)

    def test_ingestion_api_flow(self):
        # Submit valid educational URL
        submit_res = client.post(
            "/api/v1/content/ingestion/submit",
            headers=self.teacher_headers,
            json={
                "url": "https://www.khanacademy.org/science/biology/cellular-respiration",
                "title": "Cellular Respiration and ATP Synthesis",
                "description": "Comprehensive explanation of glycolysis, Krebs cycle, and mitochondria electron transport.",
                "board": "CBSE",
                "content_type": "reading"
            }
        )
        self.assertEqual(submit_res.status_code, 201)
        data = submit_res.json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["content_item_id"])

        # Check pending queue or approved list
        pending_res = client.get(
            "/api/v1/content/ingestion/pending",
            headers=self.teacher_headers
        )
        self.assertEqual(pending_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
