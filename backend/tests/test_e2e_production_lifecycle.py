import unittest
import datetime
import os
import sys
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.models import (
    School, User, StudentProfile, StudentProgress, QuizAttempt, Quiz, Question,
    ContentItem, SpacedRepetitionSchedule, ParentalConsentLog, SchoolClass,
    teacher_classes, parent_student_links, ConsentRecord
)
from app.core.age_policy import ProcessingPurpose
from app.core.security import get_password_hash
from app.embeddings.embedder import embed_content

client = TestClient(app)

class TestE2EProductionLifecycle(unittest.TestCase):
    """
    Deterministic End-to-End Production Lifecycle Verification Suite:
    Validates all 20 steps of the real Edufeedia educational feedback loop
    with isolated fixtures and complete cleanup.
    """
    CLASS_ID = "cls-e2e-isolated"
    SCHOOL_ID = "sch-e2e-isolated"
    TEACHER_ID = "u-teacher-e2e-det"
    TEACHER_EMAIL = "teacher_e2e_det@apexschool.edu"
    PARENT_ID = "u-parent-e2e-det"
    PARENT_EMAIL = "parent_e2e_det@gmail.com"
    STUDENT_EMAIL = "student_e2e_det@apexschool.edu"
    CONTENT_ID = "c-e2e-physics-lesson"
    QUIZ_ID = "q-e2e-physics-quiz"

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls._cleanup_all(cls.db)

        # 0. Dedicated School Fixture
        cls.school = cls.db.query(School).filter(School.id == cls.SCHOOL_ID).first()
        if not cls.school:
            cls.school = School(
                id=cls.SCHOOL_ID,
                name="E2E Testing Academy",
                domain="e2eschool.edu",
                address="Testing Lab"
            )
            cls.db.add(cls.school)
            cls.db.flush()

        # 1. Dedicated School Class Fixture
        cls.school_class = SchoolClass(
            id=cls.CLASS_ID,
            school_id=cls.SCHOOL_ID,
            grade_level=10,
            section_name="E2E",
            academic_year="2026-2027"
        )
        cls.db.add(cls.school_class)

        # 2. Dedicated Teacher Fixture
        cls.teacher_user = User(
            id=cls.TEACHER_ID,
            email=cls.TEACHER_EMAIL,
            password_hash=get_password_hash("Teacher123!"),
            role="teacher",
            first_name="Priya",
            last_name="Sharma",
            is_verified=True,
            school_id=cls.SCHOOL_ID
        )
        cls.db.add(cls.teacher_user)
        cls.db.flush()

        cls.db.execute(
            teacher_classes.insert().values(
                teacher_user_id=cls.teacher_user.id,
                class_id=cls.school_class.id,
                subject="Science"
            )
        )

        # 3. Dedicated Parent Fixture
        cls.parent_user = User(
            id=cls.PARENT_ID,
            email=cls.PARENT_EMAIL,
            password_hash=get_password_hash("Parent123!"),
            role="parent",
            first_name="Rajesh",
            last_name="Kumar"
        )
        cls.db.add(cls.parent_user)

        # 4. Dedicated Content Item Fixture
        emb = embed_content(
            title="Newton's Laws of Motion & Forces",
            description="Comprehensive guide to inertia, acceleration, and action-reaction pairs for Class 10.",
            subject="Science",
            topic="Physics",
            tags=["Physics", "Science", "Force", "Newton", "CBSE"]
        )
        cls.content_item = ContentItem(
            id=cls.CONTENT_ID,
            title="Newton's Laws of Motion & Forces",
            description="Comprehensive guide to inertia, acceleration, and action-reaction pairs for Class 10.",
            source_url="https://www.khanacademy.org/science/class-10-physics/newtons-laws",
            source_platform="khan_academy",
            embed_code='<iframe src="https://www.khanacademy.org/embed"></iframe>',
            type="video",
            board="CBSE",
            grade_level=10,
            subject="Science",
            topic="Physics",
            difficulty="medium",
            duration_minutes=15,
            safety_score=98,
            edu_score=95,
            is_approved=True,
            tags=["Physics", "Science", "Force", "Newton", "CBSE"],
            embedding=emb
        )
        cls.db.add(cls.content_item)
        cls.db.flush()

        # 5. Dedicated Quiz & Questions Fixtures
        cls.quiz = Quiz(
            id=cls.QUIZ_ID,
            content_item_id=cls.content_item.id,
            title="Newton's Laws Diagnostic Quiz"
        )
        cls.db.add(cls.quiz)
        cls.db.flush()

        cls.q1 = Question(
            id="ques-e2e-1",
            quiz_id=cls.quiz.id,
            question_text="What is the standard formula representing Newton's Second Law?",
            options=["F = m * a", "E = m * c^2", "V = I * R", "P = W / t"],
            correct_answer="F = m * a",
            explanation="Newton's second law states that Force equals mass multiplied by acceleration (F = ma).",
            difficulty="easy"
        )
        cls.q2 = Question(
            id="ques-e2e-2",
            quiz_id=cls.quiz.id,
            question_text="Which law explains why passengers lean backward when a stationary vehicle accelerates forward?",
            options=["Law of Inertia (First Law)", "Second Law", "Third Law", "Law of Gravitation"],
            correct_answer="Law of Inertia (First Law)",
            explanation="The law of inertia explains resistance to change in velocity.",
            difficulty="medium"
        )
        cls.db.add_all([cls.q1, cls.q2])
        cls.db.commit()

    @classmethod
    def _cleanup_all(cls, db: Session):
        try:
            # Delete any created student
            student = db.query(User).filter(User.email == cls.STUDENT_EMAIL).first()
            if student:
                db.execute(parent_student_links.delete().where(parent_student_links.c.student_user_id == student.id))
                db.query(ConsentRecord).filter(ConsentRecord.student_user_id == student.id).delete()
                db.query(ParentalConsentLog).filter(ParentalConsentLog.student_user_id == student.id).delete()
                db.query(QuizAttempt).filter(QuizAttempt.student_user_id == student.id).delete()
                db.query(StudentProgress).filter(StudentProgress.student_user_id == student.id).delete()
                db.query(SpacedRepetitionSchedule).filter(SpacedRepetitionSchedule.student_user_id == student.id).delete()
                db.query(StudentProfile).filter(StudentProfile.user_id == student.id).delete()
                db.delete(student)

            # Delete teacher & classes
            teacher = db.query(User).filter(User.id == cls.TEACHER_ID).first()
            if teacher:
                db.execute(teacher_classes.delete().where(teacher_classes.c.teacher_user_id == teacher.id))
                db.delete(teacher)

            # Delete parent
            parent = db.query(User).filter(User.id == cls.PARENT_ID).first()
            if parent:
                db.execute(parent_student_links.delete().where(parent_student_links.c.parent_user_id == parent.id))
                db.delete(parent)

            # Delete questions, quiz, content, school class, school
            db.query(Question).filter(Question.quiz_id == cls.QUIZ_ID).delete()
            db.query(Quiz).filter(Quiz.id == cls.QUIZ_ID).delete()
            db.query(ContentItem).filter(ContentItem.id == cls.CONTENT_ID).delete()
            db.query(SchoolClass).filter(SchoolClass.id == cls.CLASS_ID).delete()
            db.query(School).filter(School.id == cls.SCHOOL_ID).delete()
            
            # Clean any staged content ingested during test
            staged_items = db.query(ContentItem).filter(ContentItem.title == "Laws of Motion & Force Demonstration").all()
            for it in staged_items:
                db.delete(it)

            db.commit()
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"[E2E Cleanup Failure]: Failed to clean test fixtures: {e}") from e

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_all(cls.db)
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
        reg_res = client.post("/api/v1/auth/register", json={
            "email": self.STUDENT_EMAIL,
            "password": "Password123!",
            "first_name": "Aarav",
            "last_name": "Patel",
            "role": "student",
            "date_of_birth": "2010-05-15",
            "board": "CBSE",
            "school_id": self.SCHOOL_ID,
            "class_id": self.school_class.id
        })
        self.assertEqual(reg_res.status_code, 201)
        student_id = reg_res.json()["id"]

        # Link parent to student with verified consent
        self.db.execute(
            parent_student_links.insert().values(
                parent_user_id=self.parent_user.id,
                student_user_id=student_id,
                is_verified=True
            )
        )
        # Create granular verified ConsentRecords for all student processing purposes
        for purp in [ProcessingPurpose.AI_SOCRATIC_TUTOR, ProcessingPurpose.PERSONALIZED_RECOMMENDATIONS, ProcessingPurpose.FORMATIVE_PROGRESS_TRACKING, ProcessingPurpose.ANALYTICS_AGGREGATION]:
            self.db.add(ConsentRecord(
                student_user_id=student_id,
                guardian_user_id=self.parent_user.id,
                processing_purpose=purp.value,
                consent_scope=purp.value,
                status="ACTIVE",
                verification_method="GUARDIAN_EMAIL_OTP",
                policy_version="2026.2-DPDP"
            ))

        consent_log = ParentalConsentLog(
            student_user_id=student_id,
            parent_user_id=self.parent_user.id,
            parent_email=self.parent_user.email,
            consent_status="granted",
            verification_method="email_verification",
            consent_scope=["curriculum_access", "ai_socratic_tutor", "analytics_tracking"]
        )
        self.db.add(consent_log)
        sp = self.db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        st_user = self.db.query(User).filter(User.id == student_id).first()
        if sp:
            sp.school_id = self.SCHOOL_ID
            sp.class_id = self.CLASS_ID
            sp.parental_consent_status = "GRANTED"
            sp.onboarding_status = "COMPLETED"
        if st_user:
            st_user.school_id = self.SCHOOL_ID
        self.db.commit()

        # 3. Login as Student
        login_res = client.post("/api/v1/auth/login", json={
            "email": self.STUDENT_EMAIL,
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

        # 5. Open Dedicated Lesson Details
        lesson_res = client.get(f"/api/v1/content/{self.CONTENT_ID}", headers=student_headers)
        self.assertEqual(lesson_res.status_code, 200)
        self.assertEqual(lesson_res.json()["id"], self.CONTENT_ID)
        self.assertEqual(lesson_res.json()["topic"], "Physics")

        # 6. Complete Lesson & Log Progress
        prog_res = client.post("/api/v1/content/progress", headers=student_headers, json={
            "content_item_id": self.CONTENT_ID,
            "progress_percentage": 100
        })
        self.assertEqual(prog_res.status_code, 200)
        self.assertEqual(prog_res.json()["status"], "success")
        self.assertTrue(prog_res.json()["completed"])

        # 7. Fetch Assessment Quiz for Lesson
        quiz_res = client.get(f"/api/v1/quizzes/content/{self.CONTENT_ID}", headers=student_headers)
        self.assertEqual(quiz_res.status_code, 200)
        quiz_data = quiz_res.json()
        self.assertEqual(quiz_data["id"], self.QUIZ_ID)
        self.assertEqual(len(quiz_data["questions"]), 2)

        # Verify Answer Key Security: Questions in GET quiz must NOT leak correct_answer
        for q in quiz_data["questions"]:
            self.assertNotIn("correct_answer", q)
            self.assertNotIn("explanation", q)

        # 8. Submit Quiz Attempt with Authoritative Answers
        submit_res = client.post("/api/v1/quizzes/submit", headers=student_headers, json={
            "quiz_id": self.QUIZ_ID,
            "answers": [
                {"question_id": "ques-e2e-1", "selected_answer": "F = m * a"},
                {"question_id": "ques-e2e-2", "selected_answer": "Law of Inertia (First Law)"}
            ]
        })
        self.assertEqual(submit_res.status_code, 200)
        eval_result = submit_res.json()
        self.assertEqual(eval_result["score"], 2)
        self.assertEqual(eval_result["max_score"], 2)
        self.assertEqual(eval_result["accuracy_percentage"], 100.0)
        self.assertGreaterEqual(eval_result["xp_gained"], 20)

        # 9. Verify QuizAttempt Record in Database
        attempt_db = self.db.query(QuizAttempt).filter(
            QuizAttempt.student_user_id == student_id,
            QuizAttempt.quiz_id == self.QUIZ_ID
        ).first()
        self.assertIsNotNone(attempt_db)
        self.assertEqual(attempt_db.score, 2)
        self.assertEqual(attempt_db.accuracy_percentage, 100.0)

        # 10. Verify XP Updated in StudentProfile
        profile_db = self.db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        self.assertIsNotNone(profile_db)
        self.assertGreaterEqual(profile_db.xp_score, eval_result["xp_gained"])

        # 11. Verify SM-2 Spaced Repetition Schedule Created
        schedule_db = self.db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student_id,
            SpacedRepetitionSchedule.topic == "Physics"
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
            "question": "Can you explain how inertia connects to mass?",
            "content_item_id": self.CONTENT_ID
        })
        self.assertEqual(tutor_res.status_code, 200)
        tutor_data = tutor_res.json()
        self.assertTrue(tutor_data["is_safe"])
        self.assertIn("socratic_cue", tutor_data)

        # 14. Login as Parent
        parent_login = client.post("/api/v1/auth/login", json={
            "email": self.PARENT_EMAIL,
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
            "email": self.TEACHER_EMAIL,
            "password": "Teacher123!"
        })
        self.assertEqual(teacher_login.status_code, 200)
        teacher_headers = {"Authorization": f"Bearer {teacher_login.json()['access_token']}"}

        # 17. Verify Teacher Class Roster & Aggregated Analytics
        classes_res = client.get("/api/v1/teachers/classes", headers=teacher_headers)
        self.assertEqual(classes_res.status_code, 200)
        classes_list = classes_res.json()
        self.assertGreater(len(classes_list), 0)

        analytics_res = client.get(f"/api/v1/teachers/classes/{self.CLASS_ID}/analytics", headers=teacher_headers)
        self.assertEqual(analytics_res.status_code, 200)
        class_analytics = analytics_res.json()
        self.assertIn("class_average_accuracy", class_analytics)
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
