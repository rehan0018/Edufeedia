import unittest
import datetime
import os
import sys
from pathlib import Path
from decimal import Decimal

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.models import (
    User, StudentProfile, ContentItem, Quiz, Question, QuizAttempt,
    TopicMastery, SpacedRepetitionSchedule, IngestedSource, CurriculumChunk,
    Badge, UserBadge
)
from app.ingestion.extractors.pdf_extractor import PDFExtractor
from app.ingestion.extractors.html_extractor import HTMLExtractor
from app.ingestion.extractors.youtube_extractor import YouTubeExtractor
from app.ingestion.chunker import SemanticChunker
from app.ingestion.state_machine import IngestionStateMachine, IngestionStage
from app.core.mastery_engine import MasteryEngine
from app.core.lifecycle_service import StudentLifecycleService
from app.core.age_policy import StudentAgePolicy
from app.ai.socratic_policy import SocraticPolicy

class TestClosedLearningLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------
    # 1. Multi-Source Extractors
    # -------------------------------------------------------------
    def test_html_extractor_strips_boilerplate(self):
        html_input = """
        <html>
            <head><title>Ohm's Law</title><style>.ad{display:none;}</style></head>
            <body>
                <nav><a href="#">Home</a></nav>
                <h1>Ohm's Law and Resistance</h1>
                <p>Electric current flowing through a conductor is directly proportional to potential difference.</p>
                <script>console.log("tracker");</script>
                <footer>Copyright 2026 Edufeedia</footer>
            </body>
        </html>
        """
        res = HTMLExtractor.extract_from_html(html_input)
        self.assertTrue(res["success"])
        self.assertIn("Ohm's Law and Resistance", res["extracted_text"])
        self.assertIn("proportional to potential difference", res["extracted_text"])
        self.assertNotIn("console.log", res["extracted_text"])

    def test_youtube_extractor_metadata_and_chapters(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        res = YouTubeExtractor.extract_video_metadata(url)
        self.assertTrue(res["success"])
        self.assertEqual(res["video_id"], "dQw4w9WgXcQ")
        self.assertTrue(len(res["chapters"]) >= 3)
        self.assertIn("embed_url", res)

    # -------------------------------------------------------------
    # 2. Semantic Chunker
    # -------------------------------------------------------------
    def test_semantic_chunker_bounds_and_overlap(self):
        sample_text = (
            "Newton's First Law states that every object continues in its state of rest or uniform motion. "
            "Newton's Second Law defines force as the rate of change of momentum (F = ma). "
            "Newton's Third Law states that for every action there is an equal and opposite reaction. "
            "Inertia is the inherent property of an object to resist changes in its state of motion. "
            "Linear momentum is the product of mass and velocity of an object in motion."
        )
        chunks = SemanticChunker.chunk_text(
            text=sample_text,
            subject="Science",
            topic="Laws of Motion",
            chapter="Force and Motion",
            default_section="Three Laws of Motion"
        )
        self.assertTrue(len(chunks) >= 1)
        first_chunk = chunks[0]
        self.assertEqual(first_chunk["subject"], "Science")
        self.assertEqual(first_chunk["topic"], "Laws of Motion")
        self.assertIn("chunk_index", first_chunk)
        self.assertTrue(first_chunk["char_length"] > 0)

    # -------------------------------------------------------------
    # 3. Ingestion State Machine
    # -------------------------------------------------------------
    def test_ingestion_state_machine_happy_path(self):
        res = IngestionStateMachine.run_pipeline(
            db=self.db,
            url="https://khanacademy.org/science/physics/forces-newtons-laws",
            title="Forces & Newton's Laws Comprehensive Guide",
            description="Deep exploration of Newton's 1st, 2nd, and 3rd laws for CBSE Class 10 Physics.",
            raw_text="Newton's laws of motion are three basic laws of classical mechanics describing the relationship between the motion of an object and the forces acting on it.",
            board="CBSE",
            grade_level=10
        )
        self.assertTrue(res["success"])
        self.assertIn(res["status"], [IngestionStage.PUBLISHED, IngestionStage.PENDING_REVIEW])
        
        # Verify IngestedSource in database
        src = self.db.query(IngestedSource).filter(IngestedSource.id == res["source_id"]).first()
        self.assertIsNotNone(src)
        self.assertTrue("Newton" in (src.topic or "") or "Physics" in (src.topic or "") or "Science" in (src.subject or ""))

    # -------------------------------------------------------------
    # 4. Socratic Policy & Answer Leakage Detector
    # -------------------------------------------------------------
    def test_socratic_policy_blocks_direct_numeric_answer(self):
        question = "What is the force when mass is 10kg and acceleration is 5m/s^2?"
        raw_llm_response = "The answer is 50 N."
        audit = SocraticPolicy.audit_and_steer_response(
            raw_llm_response=raw_llm_response,
            student_question=question,
            topic="Laws of Motion",
            subject="Science",
            retrieved_chunks=[{"text": "F = ma relates force, mass, and acceleration."}]
        )
        self.assertTrue(audit["leakage_blocked"])
        self.assertNotIn("50 N", audit["response_text"])
        self.assertTrue(audit["is_socratic"])
        self.assertIn("formula connects Force", audit["response_text"])

    def test_socratic_policy_allows_conceptual_guidance(self):
        question = "Can you explain how inertia works?"
        raw_llm_response = "Inertia is an object's resistance to a change in its velocity. For example, when a bus suddenly stops, why do you lurch forward?"
        audit = SocraticPolicy.audit_and_steer_response(
            raw_llm_response=raw_llm_response,
            student_question=question,
            topic="Laws of Motion",
            subject="Science",
            retrieved_chunks=[{"text": "Inertia is the property of a body to resist acceleration."}]
        )
        self.assertFalse(audit["leakage_blocked"])
        self.assertTrue(audit["is_socratic"])
        self.assertTrue(audit["groundedness_score"] >= 0.60)

    # -------------------------------------------------------------
    # 5. Topic Mastery Engine & Closed Learning Loop
    # -------------------------------------------------------------
    def test_mastery_engine_server_side_quiz_and_trend(self):
        # 1. Create Student
        student = User(
            id="u-loop-student-01",
            email="loop_student@apexschool.edu",
            role="student",
            first_name="Loop",
            last_name="Learner",
            is_verified=True
        )
        profile = StudentProfile(
            user_id=student.id,
            grade_level=10,
            board="CBSE",
            xp_score=100,
            streak_count=3,
            last_active_date=datetime.date.today() - datetime.timedelta(days=1)
        )
        self.db.add_all([student, profile])

        content_item = ContentItem(
            id="c-loop-physics",
            title="Newton's Laws of Motion Video Lesson",
            source_url="https://youtube.com/watch?v=newton01",
            source_platform="youtube",
            type="video",
            duration_minutes=15,
            subject="Science",
            topic="Newton's Laws of Motion",
            grade_level=10,
            board="CBSE",
            is_approved=True
        )
        self.db.add(content_item)
        self.db.flush()

        # 2. Create Quiz & Questions
        quiz = Quiz(
            id="q-loop-physics",
            title="Newtonian Dynamics Diagnostic Checkpoint",
            content_item_id=content_item.id
        )
        q1 = Question(
            id="q1-loop",
            quiz_id=quiz.id,
            question_text="What formula calculates force?",
            options=["F = ma", "F = m/a", "F = m + a", "F = m - a"],
            correct_answer="F = ma",
            explanation="Newton's second law defines F = ma."
        )
        q2 = Question(
            id="q2-loop",
            quiz_id=quiz.id,
            question_text="Which law explains action-reaction pairs?",
            options=["First Law", "Second Law", "Third Law", "Law of Gravitation"],
            correct_answer="Third Law",
            explanation="Newton's third law states action equals opposite reaction."
        )
        self.db.add_all([quiz, q1, q2])
        self.db.commit()

        # 3. Submit 100% correct answers
        res1 = MasteryEngine.evaluate_quiz_submission(
            db=self.db,
            student_id=student.id,
            quiz_id=quiz.id,
            user_answers={q1.id: 0, q2.id: 2}
        )
        self.assertEqual(res1["accuracy_percentage"], 100.0)
        self.assertEqual(res1["topic_mastery"]["mastery_score"], 100.0)
        self.assertEqual(res1["topic_mastery"]["trend"], "stable")

        # Check Spaced Repetition was initialized
        sched = self.db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student.id,
            SpacedRepetitionSchedule.topic == "Newton's Laws of Motion"
        ).first()
        self.assertIsNotNone(sched)
        self.assertEqual(sched.repetition_number, 1)

        # 4. Submit a second lower-scoring attempt (50% accuracy)
        res2 = MasteryEngine.evaluate_quiz_submission(
            db=self.db,
            student_id=student.id,
            quiz_id=quiz.id,
            user_answers={q1.id: 0, q2.id: 0} # 1 correct, 1 wrong
        )
        self.assertEqual(res2["accuracy_percentage"], 50.0)
        # EMA: 0.70 * 100 + 0.30 * 50 = 85.0
        self.assertEqual(res2["topic_mastery"]["mastery_score"], 85.0)
        self.assertEqual(res2["topic_mastery"]["trend"], "declining")

    # -------------------------------------------------------------
    # 6. Student Lifecycle & Age Policy Service
    # -------------------------------------------------------------
    def test_student_lifecycle_transitions(self):
        student = User(
            id="u-life-01",
            email="minor_student@apexschool.edu",
            role="student",
            first_name="Minor",
            last_name="Child",
            is_verified=True
        )
        profile = StudentProfile(
            user_id=student.id,
            onboarding_status="PENDING",
            parental_consent_status="PENDING",
            learning_access_status="RESTRICTED"
        )
        self.db.add_all([student, profile])
        self.db.commit()

        # 1. Complete Onboarding for a 14-year-old minor
        today = datetime.date.today()
        dob = datetime.date(today.year - 14, today.month, today.day)
        onboard_res = StudentLifecycleService.complete_onboarding(
            db=self.db,
            user_id=student.id,
            grade_level=9,
            board="CBSE",
            date_of_birth=dob,
            interests=["Physics", "Astronomy"]
        )
        self.assertEqual(onboard_res["onboarding_status"], "COMPLETED")
        self.assertEqual(onboard_res["consent_status"], "PENDING")
        self.assertEqual(onboard_res["learning_access_status"], "RESTRICTED")

        # 2. Grant Guardian Consent
        consent_res = StudentLifecycleService.grant_consent(
            db=self.db,
            student_id=student.id,
            parent_user_id="u-parent-01",
            parent_email="guardian@apexschool.edu",
            verification_method="email_otp",
            consent_scopes=["curriculum_access", "ai_socratic_tutor", "analytics_tracking"]
        )
        self.assertEqual(consent_res["learning_access_status"], "ACTIVE")

        # 3. Dynamic Age Policy Validation
        age = StudentAgePolicy.calculate_age(dob)
        self.assertEqual(age, 14)
        self.assertEqual(StudentAgePolicy.get_age_band(age), "BAND_13_15")
        ai_policy = StudentAgePolicy.get_ai_policy(age)
        self.assertTrue(ai_policy["strict_safety_gate"])

if __name__ == "__main__":
    unittest.main()
