import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestPhase3Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Login as Student
        s_res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        assert s_res.status_code == 200
        cls.student_headers = {"Authorization": f"Bearer {s_res.json()['access_token']}"}

        # 2. Login as Teacher
        t_res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        assert t_res.status_code == 200
        cls.teacher_headers = {"Authorization": f"Bearer {t_res.json()['access_token']}"}

    def test_explore_catalog_search_and_filter(self):
        # Search for 'network'
        res = client.get("/api/v1/content/explore?query=network", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertGreater(len(items), 0)
        self.assertTrue(any("network" in item["title"].lower() or "network" in item["topic"].lower() for item in items))

        # Filter by Subject 'Computer Science'
        cs_res = client.get("/api/v1/content/explore?subject=Computer%20Science", headers=self.student_headers)
        self.assertEqual(cs_res.status_code, 200)
        cs_items = cs_res.json()
        self.assertGreater(len(cs_items), 0)
        self.assertTrue(all(item["subject"] == "Computer Science" for item in cs_items))

    def test_inter_class_weekly_challenge(self):
        res = client.get("/api/v1/challenges/weekly", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("title", data)
        self.assertIn("days_remaining", data)
        self.assertIn("target_class_xp", data)

    def test_inter_class_leaderboard_under18_safe(self):
        res = client.get("/api/v1/challenges/class-leaderboard", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        leaderboard = res.json()
        self.assertGreater(len(leaderboard), 0)
        # Verify it lists class teams (e.g. Class 10A), NOT individual student full names
        for item in leaderboard:
            self.assertIn("class_name", item)
            self.assertIn("total_xp", item)
            self.assertIn("average_accuracy", item)
            self.assertNotIn("student_name", item)

    def test_private_personal_growth(self):
        res = client.get("/api/v1/challenges/my-growth", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("monthly_improvement_percentage", data)
        self.assertIn("growth_statement", data)
        self.assertIn("current_xp", data)

    def test_teacher_ai_quiz_draft_generation(self):
        # Teacher generates draft questions for review
        res = client.post(
            "/api/v1/quizzes/generate-draft",
            headers=self.teacher_headers,
            json={
                "subject": "Computer Science",
                "topic": "Computer Networks",
                "grade_level": 10,
                "num_questions": 3
            }
        )
        self.assertEqual(res.status_code, 200)
        draft = res.json()
        self.assertEqual(len(draft), 3)
        for q in draft:
            self.assertIn("question_text", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["correct_answer"], q["options"])
            self.assertIn("blooms_level", q)

    def test_teacher_custom_quiz_authoring_and_publishing(self):
        # Teacher authors and publishes a custom assessment
        res = client.post(
            "/api/v1/quizzes/custom",
            headers=self.teacher_headers,
            json={
                "title": "Custom Networks Mastery Check",
                "subject": "Computer Science",
                "topic": "Computer Networks",
                "grade_level": 10,
                "questions": [
                    {
                        "question_text": "What does LAN stand for in computer networking?",
                        "options": [
                            "Local Area Network",
                            "Long Array Network",
                            "Logical Access Node",
                            "Linear Audio Network"
                        ],
                        "correct_answer": "Local Area Network",
                        "explanation": "LAN stands for Local Area Network.",
                        "difficulty": "easy",
                        "blooms_level": "Remember"
                    }
                ]
            }
        )
        self.assertEqual(res.status_code, 201)
        quiz = res.json()
        self.assertEqual(quiz["title"], "Custom Networks Mastery Check")
        self.assertEqual(len(quiz["questions"]), 1)

if __name__ == "__main__":
    unittest.main()
