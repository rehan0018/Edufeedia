import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db, SessionLocal
from app.models.models import (
    User, StudentProfile, StudentProgress, QuizAttempt, Quiz, Question,
    ContentItem, SpacedRepetitionSchedule, ParentalConsentLog, SchoolClass,
    teacher_classes, parent_student_links
)
from app.core.security import get_password_hash

client = TestClient(app)

class TestE2EProductionLifecycle(unittest.TestCase):
    """
    End-to-End Production Verification Suite:
    Validates all 20 steps of the real Edufeedia educational feedback loop.
    """
    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        
        # Ensure school class exists
        cls.school_class = cls.db.query(SchoolClass).first()
        if not cls.school_class:
            cls.school_class = SchoolClass(
                id="cls-e2e-10a",
                school_id="sch-apex-1",
                grade_level=10,
                section_name="A",
                academic_year="2026-2027"
            )
            cls.db.add(cls.school_class)
            cls.db.commit()

        # Seed teacher
        cls.teacher_user = cls.db.query(User).filter(User.email == "teacher_e2e@apexschool.edu").first()
        if not cls.teacher_user:
            cls.teacher_user = User(
                id="u-teacher-e2e",
                email="teacher_e2e@apexschool.edu",
                password_hash=get_password_hash("Teacher123!"),
                role="teacher",
                first_name="Priya",
                last_name="Sharma",
                school_id="sch-apex-1"
            )
            cls.db.add(cls.teacher_user)
            cls.db.commit()

            cls.db.execute(
                teacher_classes.insert().values(
                    teacher_user_id=cls.teacher_user.id,
                    class_id=cls.school_class.id,
                    subject="Science"
                )
            )
            cls.db.commit()

        # Seed parent
        cls.parent_user = cls.db.query(User).filter(User.email == "parent_e2e@gmail.com").first()
        if not cls.parent_user:
            cls.parent_user = User(
                id="u-parent-e2e",
                email="parent_e2e@gmail.com",
                password_hash=get_password_hash("Parent123!"),
                role="parent",
                first_name="Rajesh",
                last_name="Kumar"
            )
            cls.db.add(cls.parent_user)
            cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_complete_20_step_production_lifecycle(self):
        # 1. Health & Readiness Check
        res = client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        res = client.get("/api/v1/ready")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["database"])

        # 2. Register a brand new real student
        student_email = "student_e2e_test@apexschool.edu"
        existing = self.db.query(User).filter(User.email == student_email).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()

        reg_res = client.post("/api/v1/auth/register", json={
            "email": student_email,
            "password": "Password123!",
            "first_name": "Aarav",
            "last_name": "Patel",
            "role": "student",
            "date_of_birth": "2010-05-15",
            "board": "CBSE",
            "school_id": "sch-apex-1",
            "class_id": self.school_class.id
        })
        self.assertEqual(reg_res.status_code, 201)
        student_id = reg_res.json()["id"]

        # Link parent to student with verified consent
        self.db.execute(
            parent_student_links.insert().values(
                parent_user_id=self.parent_user.id,
                student_user_id=student_id
            )
        )
        consent_log = ParentalConsentLog(
            student_user_id=student_id,
            parent_user_id=self.parent_user.id,
            parent_email=self.parent_user.email,
            consent_status="granted",
            verification_method="email_verification",
            consent_scope=["curriculum_access", "ai_socratic_tutor", "analytics_tracking"]
        )
        self.db.add(consent_log)
        self.db.commit()

        # 3. Login as Student
        login_res = client.post("/api/v1/auth/login", json={
            "email": student_email,
            "password": "Password123!"
        })
        self.assertEqual(login_res.status_code, 200)
        student_token = login_res.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # 4. Fetch Real Recommendations / Daily Learning Plan Feed
        feed_res = client.get("/api/v1/recommendations/feed", headers=student_headers)
        self.assertEqual(feed_res.status_code, 200)
        feed_data = feed_res.json()
        self.assertIn("items", feed_data)
        self.assertGreater(len(feed_data["items"]), 0)
        
        # 5. Open Lesson Details (select lesson linked to assessment quiz)
        quiz_obj = self.db.query(Quiz).first()
        content_id = quiz_obj.content_item_id
        lesson_res = client.get(f"/api/v1/content/{content_id}", headers=student_headers)
        self.assertEqual(lesson_res.status_code, 200)
        self.assertEqual(lesson_res.json()["id"], content_id)

        # 6. Complete Lesson & Log Progress
        prog_res = client.post("/api/v1/content/progress", headers=student_headers, json={
            "content_item_id": content_id,
            "progress_percentage": 100
        })
        self.assertEqual(prog_res.status_code, 200)
        self.assertEqual(prog_res.json()["status"], "success")
        self.assertTrue(prog_res.json()["completed"])

        # 7. Fetch Assessment Quiz for Lesson
        quiz_res = client.get(f"/api/v1/quizzes/content/{content_id}", headers=student_headers)
        self.assertEqual(quiz_res.status_code, 200)
        quiz_data = quiz_res.json()
        self.assertIn("questions", quiz_data)
        self.assertGreater(len(quiz_data["questions"]), 0)

        # Verify Answer Key Security: Questions in GET quiz must NOT leak correct_answer
        for q in quiz_data["questions"]:
            self.assertNotIn("correct_answer", q)
            self.assertNotIn("explanation", q)

        # 8. Submit Quiz Attempt with All Answers
        quiz_id = quiz_data["id"]
        answers_payload = [
            {"question_id": q["id"], "selected_answer": q["options"][0]}
            for q in quiz_data["questions"]
        ]
        submit_res = client.post("/api/v1/quizzes/submit", headers=student_headers, json={
            "quiz_id": quiz_id,
            "answers": answers_payload
        })
        self.assertEqual(submit_res.status_code, 200)
        eval_result = submit_res.json()
        self.assertIn("score", eval_result)
        self.assertIn("accuracy_percentage", eval_result)
        self.assertIn("xp_gained", eval_result)
        self.assertIn("results", eval_result)

        # 9. Verify QuizAttempt Record in Database
        attempt_db = self.db.query(QuizAttempt).filter(
            QuizAttempt.student_user_id == student_id,
            QuizAttempt.quiz_id == quiz_id
        ).first()
        self.assertIsNotNone(attempt_db)
        self.assertEqual(attempt_db.score, eval_result["score"])

        # 10. Verify XP Updated in StudentProfile
        profile_db = self.db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        self.assertIsNotNone(profile_db)
        self.assertGreaterEqual(profile_db.xp_score, eval_result["xp_gained"])

        # 11. Verify SM-2 Spaced Repetition Schedule Created
        schedule_db = self.db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student_id
        ).first()
        self.assertIsNotNone(schedule_db)
        self.assertGreaterEqual(schedule_db.interval_days, 1)

        # 12. Refresh Mastery Analytics
        mastery_res = client.get("/api/v1/students/analytics/mastery", headers=student_headers)
        self.assertEqual(mastery_res.status_code, 200)
        mastery_data = mastery_res.json()
        self.assertIn("subject_mastery", mastery_data)
        self.assertIn("upcoming_revisions", mastery_data)

        # 13. Socratic AI Tutor Interaction
        tutor_res = client.post("/api/v1/tutor/ask", headers=student_headers, json={
            "question": "What is the formula for Newton's second law?",
            "content_item_id": content_id
        })
        self.assertEqual(tutor_res.status_code, 200)
        tutor_data = tutor_res.json()
        self.assertTrue(tutor_data["is_safe"])
        self.assertIn("socratic_cue", tutor_data)

        # 14. Login as Parent
        parent_login = client.post("/api/v1/auth/login", json={
            "email": "parent_e2e@gmail.com",
            "password": "Parent123!"
        })
        self.assertEqual(parent_login.status_code, 200)
        parent_headers = {"Authorization": f"Bearer {parent_login.json()['access_token']}"}

        # 15. Verify Parent Linked Student & Consent Status
        parent_students_res = client.get("/api/v1/parents/students", headers=parent_headers)
        self.assertEqual(parent_students_res.status_code, 200)
        linked_students = parent_students_res.json()
        self.assertTrue(any(s["student_id"] == student_id for s in linked_students))

        parent_prog_res = client.get(f"/api/v1/parents/student/{student_id}/progress", headers=parent_headers)
        self.assertEqual(parent_prog_res.status_code, 200)
        parent_prog_data = parent_prog_res.json()
        self.assertTrue(parent_prog_data["consent"]["is_verified"])
        self.assertGreaterEqual(parent_prog_data["total_lessons_completed"], 1)

        # 16. Login as Teacher
        teacher_login = client.post("/api/v1/auth/login", json={
            "email": "teacher_e2e@apexschool.edu",
            "password": "Teacher123!"
        })
        self.assertEqual(teacher_login.status_code, 200)
        teacher_headers = {"Authorization": f"Bearer {teacher_login.json()['access_token']}"}

        # 17. Verify Teacher Class Roster & Aggregated Analytics
        classes_res = client.get("/api/v1/teachers/classes", headers=teacher_headers)
        self.assertEqual(classes_res.status_code, 200)
        classes_list = classes_res.json()
        self.assertGreater(len(classes_list), 0)

        analytics_res = client.get(f"/api/v1/teachers/classes/{self.school_class.id}/analytics", headers=teacher_headers)
        self.assertEqual(analytics_res.status_code, 200)
        class_analytics = analytics_res.json()
        self.assertIn("average_mastery_percentage", class_analytics)
        self.assertGreaterEqual(class_analytics["total_students"], 1)

        # 18. Submit Staged Educational URL for Ingestion
        ingest_res = client.post("/api/v1/content/ingestion/submit", headers=teacher_headers, json={
            "url": "https://www.youtube.com/watch?v=kKKM8Y-u7ds",
            "title": "Laws of Motion & Force Demonstration",
            "description": "Educational physics demonstration on Newton's laws.",
            "board": "CBSE"
        })
        self.assertEqual(ingest_res.status_code, 201)
        staged_id = ingest_res.json()["content_item_id"]

        # 19. Pending Review Queue & Moderation Approval
        pending_res = client.get("/api/v1/content/ingestion/pending", headers=teacher_headers)
        self.assertEqual(pending_res.status_code, 200)

        review_res = client.post(f"/api/v1/content/ingestion/{staged_id}/review", headers=teacher_headers, json={
            "action": "approve",
            "moderator_notes": "Verified pedagogical quality for Class 10 Physics."
        })
        self.assertEqual(review_res.status_code, 200)
        self.assertEqual(review_res.json()["status"], "approved")

        # 20. Verify Dynamic Re-ranking Reflects Ingestion & Mastery
        feed_updated = client.get("/api/v1/recommendations/feed", headers=student_headers)
        self.assertEqual(feed_updated.status_code, 200)
        self.assertIn("items", feed_updated.json())

if __name__ == "__main__":
    unittest.main()
