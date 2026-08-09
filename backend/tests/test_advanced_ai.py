import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.ai.question_generator import AIQuestionGenerator
from app.embeddings.embedder import embed_query, embed_content, cosine_similarity
from app.config import settings

client = TestClient(app)

class TestAdvancedAILayers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Authenticate as student Rahul
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        assert res.status_code == 200
        cls.student_token = res.json()["access_token"]
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

        # Authenticate as teacher
        t_res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        assert t_res.status_code == 200
        cls.teacher_token = t_res.json()["access_token"]
        cls.teacher_headers = {"Authorization": f"Bearer {cls.teacher_token}"}

    def test_ai_question_generator_direct(self):
        # Direct generator test for Physics topic
        questions = AIQuestionGenerator.generate_quiz_for_topic(
            subject="Science",
            topic="Newton's Laws",
            grade=10,
            num_questions=2
        )
        self.assertEqual(len(questions), 2)
        for q in questions:
            self.assertIn("question_text", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn("correct_answer", q)
            self.assertIn("explanation", q)
            self.assertIn("blooms_level", q)

    def test_ai_quiz_generation_endpoint(self):
        # Test POST /api/v1/quizzes/generate
        res = client.post(
            "/api/v1/quizzes/generate",
            headers=self.teacher_headers,
            json={
                "subject": "Mathematics",
                "topic": "Quadratic Equations",
                "grade_level": 10,
                "num_questions": 3
            }
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("quiz_id", data)
        self.assertEqual(data["topic"], "Quadratic Equations")
        self.assertEqual(data["total_questions"], 3)
        self.assertGreater(len(data["questions"]), 0)

    def test_semantic_vector_search_catalog(self):
        # Search using natural concept queries (e.g. cellular respiration energy ATP)
        res = client.get(
            "/api/v1/content/search?q=respiration cellular energy alveoli",
            headers=self.student_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("results", data)
        self.assertGreater(data["total_results"], 0)
        
        # Verify first match is Human Respiration / Science related
        top_match = data["results"][0]
        self.assertTrue(
            "Respiration" in top_match["title"] or top_match["subject"] == "Science"
        )
        self.assertGreater(top_match["relevance_percentage"], 35)

    def test_weak_topic_mastery_analytics(self):
        # Get diagnostic mastery report
        res = client.get(
            "/api/v1/students/analytics/mastery",
            headers=self.student_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_topics_evaluated", data)
        self.assertIn("weak_topic_count", data)
        self.assertIn("subject_mastery", data)

    def test_384d_semantic_embeddings_synonym_similarity(self):
        # 1. Verify 384-dimensional vector representation
        vec_q = embed_query("What causes acceleration in physical bodies?")
        self.assertEqual(len(vec_q), 384)

        # 2. Verify semantic synonym clustering (Newton's Second Law & Force = mass * acceleration)
        vec_concept = embed_query("Newton's second law force equals mass times acceleration")
        self.assertEqual(len(vec_concept), 384)

        sim = cosine_similarity(vec_q, vec_concept)
        self.assertGreater(sim, 0.50)

        # 3. Orthogonal topic (e.g., cell biology respiration) should have lower similarity
        vec_bio = embed_query("cellular respiration glucose ATP mitochondria")
        sim_bio = cosine_similarity(vec_q, vec_bio)
        self.assertGreater(sim, sim_bio)

    def test_multi_head_safety_classifier(self):
        from app.safety.classifier import classify_text
        
        # Test safe educational text
        edu_report = classify_text("Newton's second law defines force as mass times acceleration: F = ma.")
        self.assertIn("EDUCATIONAL_QUALITY", edu_report)
        self.assertGreater(edu_report["EDUCATIONAL_QUALITY"]["score"], 0.70)
        self.assertEqual(edu_report["TOXICITY"]["severity"], "LOW")

        # Test toxic input
        toxic_report = classify_text("You are so stupid and worthless, shut up.")
        self.assertEqual(toxic_report["TOXICITY"]["severity"], "HIGH")

    def test_security_settings_validation(self):
        # Test settings properties
        self.assertEqual(settings.ALGORITHM, "HS256")
        self.assertIsNotNone(settings.DATABASE_URL)
        self.assertTrue(len(settings.ALLOWED_ORIGINS) > 0)

if __name__ == "__main__":
    unittest.main()
