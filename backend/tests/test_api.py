import unittest
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.core.algorithms import calculate_sm2

client = TestClient(app)

class TestEdufeediaAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Run seeder to have consistent fixtures
        from seed import seed_database
        seed_database()

    def test_health_check(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "healthy")

    def test_sm2_algorithm(self):
        # Quality 5 (perfect response)
        interval, rep, ef = calculate_sm2(quality=5, prev_interval=1, prev_repetition=0, prev_easiness_factor=2.5)
        self.assertEqual(interval, 1)
        self.assertEqual(rep, 1)
        self.assertGreaterEqual(ef, 2.5)

        # Repetition 2
        interval2, rep2, ef2 = calculate_sm2(quality=4, prev_interval=interval, prev_repetition=rep, prev_easiness_factor=ef)
        self.assertEqual(interval2, 6)
        self.assertEqual(rep2, 2)

        # Poor recall (quality < 3) resets repetition
        interval_reset, rep_reset, ef_reset = calculate_sm2(quality=1, prev_interval=interval2, prev_repetition=rep2, prev_easiness_factor=ef2)
        self.assertEqual(interval_reset, 1)
        self.assertEqual(rep_reset, 0)

    def test_student_auth_and_feed(self):
        # Login as student
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "student")
        token = data["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Get feed
        feed_res = client.get("/api/v1/students/feed", headers=headers)
        self.assertEqual(feed_res.status_code, 200)
        feed_data = feed_res.json()
        self.assertIn("learning_plan", feed_data)
        self.assertIn("streak", feed_data)
        self.assertIn("xp", feed_data)

        # Get dashboard stats
        dash_res = client.get("/api/v1/students/dashboard", headers=headers)
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.json()
        self.assertIn("subject_mastery", dash_data)
        self.assertIn("average_quiz_accuracy", dash_data)

    def test_flashcard_deck_and_review(self):
        # Login as student
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get deck
        deck_res = client.get("/api/v1/flashcards/deck", headers=headers)
        self.assertEqual(deck_res.status_code, 200)
        cards = deck_res.json()
        self.assertGreater(len(cards), 0)

        # Submit review
        first_card = cards[0]
        rev_res = client.post("/api/v1/flashcards/review", headers=headers, json={
            "flashcard_id": first_card["id"],
            "rating": 4  # Easy
        })
        self.assertEqual(rev_res.status_code, 200)
        rev_data = rev_res.json()
        self.assertEqual(rev_data["status"], "success")
        self.assertGreater(rev_data["xp_earned"], 0)

    def test_explore_content(self):
        # Login as student
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        explore_res = client.get("/api/v1/content/explore?subject=Mathematics", headers=headers)
        self.assertEqual(explore_res.status_code, 200)
        items = explore_res.json()
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertIn("Mathematics", item["subject"])
            self.assertEqual(item["safety_score"], 100)

    def test_leaderboard_and_badges(self):
        # Login as student
        res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Leaderboard
        lb_res = client.get("/api/v1/students/leaderboard", headers=headers)
        self.assertEqual(lb_res.status_code, 200)
        lb = lb_res.json()
        self.assertGreater(len(lb), 1)
        # Ranks must be 1, 2, 3...
        self.assertEqual(lb[0]["rank"], 1)

        # Badges
        badges_res = client.get("/api/v1/students/badges", headers=headers)
        self.assertEqual(badges_res.status_code, 200)
        badge_data = badges_res.json()
        self.assertIn("badges", badge_data)
        self.assertGreater(badge_data["unlocked_count"], 0)

    def test_teacher_portal_endpoints(self):
        # Login as teacher
        res = client.post("/api/v1/auth/login", json={
            "email": "sharma@apexschool.edu",
            "password": "Teacher123!"
        })
        self.assertEqual(res.status_code, 200)
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get classes
        classes_res = client.get("/api/v1/teachers/classes", headers=headers)
        self.assertEqual(classes_res.status_code, 200)
        classes = classes_res.json()
        self.assertGreater(len(classes), 0)

        # Class analytics
        class_item = next(c for c in classes if c["student_count"] > 0)
        class_id = class_item["class_id"]
        analytics_res = client.get(f"/api/v1/teachers/classes/{class_id}/analytics", headers=headers)
        self.assertEqual(analytics_res.status_code, 200)
        analytics = analytics_res.json()
        self.assertEqual(analytics["class_id"], class_id)
        self.assertGreater(len(analytics["students"]), 0)

        # Create custom quiz as teacher
        quiz_res = client.post("/api/v1/teachers/quizzes", headers=headers, json={
            "title": "Teacher Special Check",
            "questions": [
                {
                    "question_text": "What is 2 + 2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": "4",
                    "explanation": "Basic addition",
                    "difficulty": "easy"
                }
            ]
        })
        self.assertEqual(quiz_res.status_code, 201)

    def test_parent_portal_endpoints(self):
        # Login as parent
        res = client.post("/api/v1/auth/login", json={
            "email": "parent@gmail.com",
            "password": "Parent123!"
        })
        self.assertEqual(res.status_code, 200)
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get linked students
        students_res = client.get("/api/v1/parents/students", headers=headers)
        self.assertEqual(students_res.status_code, 200)
        students = students_res.json()
        self.assertGreater(len(students), 0)

        # Get student progress
        student_id = students[0]["student_id"]
        prog_res = client.get(f"/api/v1/parents/student/{student_id}/progress", headers=headers)
        self.assertEqual(prog_res.status_code, 200)
        prog_data = prog_res.json()
        self.assertIn("academic_insights", prog_data)
        self.assertIn("subject_progress", prog_data)

if __name__ == "__main__":
    unittest.main()
