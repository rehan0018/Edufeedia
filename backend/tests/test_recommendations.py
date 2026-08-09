import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app
from app.safety.engine import SafetyEngine
from app.embeddings.embedder import embed_text, cosine_similarity
from app.learning.feedback import INTERACTION_WEIGHTS

client = TestClient(app)

class TestRecommendationAndSafetyEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from seed import seed_database
        seed_database()

    def test_safety_hard_gate_blocks_dangerous_content(self):
        # 1. Direct violence / explosive test
        audit1 = SafetyEngine.audit_content(
            title="How to make an explosive at home",
            description="Simple ingredients to synthesize a homemade bomb"
        )
        self.assertFalse(audit1["is_safe"])
        self.assertEqual(audit1["verdict"], "BLOCK")
        self.assertEqual(audit1["safety_score"], 0)
        self.assertIn("VIOLENCE_AND_WEAPONS", audit1["matched_rules"])

        # 2. Substance abuse test
        audit2 = SafetyEngine.audit_content(
            title="How to buy drugs online anonymously",
            description="Guide to synthesize methamphetamine and buying alcohol underage"
        )
        self.assertFalse(audit2["is_safe"])
        self.assertEqual(audit2["verdict"], "BLOCK")
        self.assertIn("DRUGS_AND_SUBSTANCES", audit2["matched_rules"])

        # 3. Fast boolean gate check
        is_safe = SafetyEngine.is_safe_for_students("Homemade pipe bomb guide")
        self.assertFalse(is_safe)

    def test_safety_engine_approves_educational_content(self):
        audit = SafetyEngine.audit_content(
            title="Introduction to Quadratic Equations",
            description="Learn standard form ax^2 + bx + c = 0, find roots using factorisation formula",
            tags=["mathematics", "algebra", "ncert"]
        )
        self.assertTrue(audit["is_safe"])
        self.assertEqual(audit["verdict"], "ALLOW")
        self.assertGreaterEqual(audit["safety_score"], 90)

    def test_semantic_embeddings_cosine_similarity(self):
        # Related programming concepts
        vec_py1 = embed_text("Introduction to Python programming functions and scope")
        vec_py2 = embed_text("Modular programming in Python with def keyword and parameters")
        sim_related = cosine_similarity(vec_py1, vec_py2)
        self.assertGreater(sim_related, 0.40)

        # Unrelated biology concept
        vec_bio = embed_text("Human cellular respiration in mitochondria and glucose breakdown")
        sim_unrelated = cosine_similarity(vec_py1, vec_bio)
        self.assertLess(sim_unrelated, sim_related)

    def test_interaction_weights_taxonomy(self):
        self.assertEqual(INTERACTION_WEIGHTS["completed"], 5.0)
        self.assertEqual(INTERACTION_WEIGHTS["bookmark"], 4.0)
        self.assertEqual(INTERACTION_WEIGHTS["like"], 3.0)
        self.assertEqual(INTERACTION_WEIGHTS["view"], 1.0)
        self.assertEqual(INTERACTION_WEIGHTS["skip"], -2.0)

    def test_recommendations_feed_api(self):
        # Login as student Rahul
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        self.assertEqual(res.status_code, 200)
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Request personalized recommendation feed
        feed_res = client.get("/api/v1/recommendations/feed", headers=headers)
        self.assertEqual(feed_res.status_code, 200)
        feed_data = feed_res.json()

        self.assertIn("items", feed_data)
        self.assertGreater(len(feed_data["items"]), 0)
        self.assertGreater(feed_data["total_candidates_evaluated"], 0)

        first_item = feed_data["items"][0]
        self.assertIn("explanation", first_item)
        exp = first_item["explanation"]
        self.assertIn("content_similarity", exp)
        self.assertIn("interest_match", exp)
        self.assertIn("grade_match", exp)
        self.assertIn("behavioral_score", exp)
        self.assertIn("total_relevance_score", exp)

    def test_log_interaction_api(self):
        # Login as student
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get a content item
        feed_res = client.get("/api/v1/recommendations/feed", headers=headers)
        item_id = feed_res.json()["items"][0]["id"]

        # Log a bookmark interaction
        inter_res = client.post("/api/v1/recommendations/interaction", headers=headers, json={
            "content_item_id": item_id,
            "interaction_type": "bookmark",
            "dwell_time_seconds": 45
        })
        self.assertEqual(inter_res.status_code, 201)
        inter_data = inter_res.json()
        self.assertEqual(inter_data["weight"], 4.0)
        self.assertEqual(inter_data["interaction_type"], "bookmark")

    def test_inspect_safety_api(self):
        # Login as teacher
        res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Inspect a hazardous prompt
        audit_res = client.post("/api/v1/recommendations/inspect-safety", headers=headers, json={
            "title": "Dangerous stunt challenge with bleach",
            "description": "Attempting illegal chemistry stunts at home",
            "target_age_group": 16
        })
        self.assertEqual(audit_res.status_code, 200)
        audit_data = audit_res.json()
        self.assertEqual(audit_data["verdict"], "BLOCK")
        self.assertFalse(audit_data["is_safe"])
        self.assertGreater(len(audit_data["categories"]), 0)

    def test_ai_socratic_tutor_api(self):
        # Login as student
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get a content item
        feed_res = client.get("/api/v1/recommendations/feed", headers=headers)
        item_id = feed_res.json()["items"][0]["id"]

        # Ask Socratic tutor
        tutor_res = client.post("/api/v1/tutor/ask", headers=headers, json={
            "content_item_id": item_id,
            "question": "Can you give me an intuitive analogy for this formula?"
        })
        self.assertEqual(tutor_res.status_code, 200)
        data = tutor_res.json()
        self.assertTrue(data["is_safe"])
        self.assertIn("answer", data)
        self.assertIn("socratic_cue", data)
        self.assertGreater(len(data["follow_up_questions"]), 0)

if __name__ == "__main__":
    unittest.main()
