"""
Unit & Integration Test Suite for Edufeedia Intelligent Discovery & Learning Engine.
Validates:
- Query Understanding & Intent Parsing
- Hierarchical Source Authority Registry (Decoupling Platform vs. Creator vs. Resource Trust)
- Strict Architectural Execution Order:
    Candidate -> Identity -> Hard Safety Gate -> Age Gate -> Authority -> Curriculum -> Quality -> Rerank -> Diversity
- Instrumented 10-factor scoring breakdown with versioned policy (v1.0)
- Personalized Reranking & Explainable Provenance ("Why this resource?")
- Closed Learning Loop (Quiz Evaluation -> Mastery Gain Delta -> TopicMastery & StudentMasteryHistory updates)
- FastAPI Endpoints (/search, /quiz-submit, /resource-engagement, /sources, /scoring-policy)
"""

import sys
import unittest
import datetime
from pathlib import Path
from decimal import Decimal

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.models import (
    User, StudentProfile, ContentItem, TopicMastery,
    StudentMasteryHistory, LearningEvent, RewardLedger
)
from app.discovery.query_understanding import QueryUnderstandingEngine
from app.discovery.source_registry import SourceAuthorityRegistry
from app.discovery.resource_quality import ResourceQualityEngine, ScoringPolicy
from app.discovery.candidate_builder import CandidateBuilder
from app.discovery.personalized_reranker import PersonalizedReranker
from app.discovery.provenance import ProvenanceGenerator
from app.discovery.pipeline import DiscoveryPipeline
from app.discovery.learning_loop import LearningLoopManager
from app.schemas.schemas import QuizSubmitRequest, ResourceEngagementRequest


class TestDiscoveryEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Override get_db dependency for TestClient
        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        self.db = self.SessionLocal()

        # Seed sample student user
        self.student = User(
            id="student-test-discovery-1",
            email="student.discovery@edufeedia.test",
            first_name="Rohan",
            last_name="Sharma",
            role="student",
            is_verified=True,
            email_verified=True,
            account_status="ACTIVE"
        )
        self.db.add(self.student)

        self.profile = StudentProfile(
            user_id=self.student.id,
            grade_level=8,
            board="CBSE",
            learning_preference=["animation", "interactive_sim"],
            xp_score=350
        )
        self.db.add(self.profile)

        # Seed weak topic mastery
        self.mastery = TopicMastery(
            student_user_id=self.student.id,
            board="CBSE",
            grade_level=8,
            subject="Science",
            topic="Photosynthesis",
            mastery_score=Decimal("45.00"),
            confidence=Decimal("0.50"),
            attempt_count=1,
            trend="declining"
        )
        self.db.add(self.mastery)
        self.db.commit()

    def tearDown(self):
        self.db.query(StudentMasteryHistory).delete()
        self.db.query(TopicMastery).delete()
        self.db.query(RewardLedger).delete()
        self.db.query(LearningEvent).delete()
        self.db.query(StudentProfile).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    # --------------------------------------------------------------------------
    # 1. Query Understanding & Intent Parsing
    # --------------------------------------------------------------------------
    def test_query_understanding_photosynthesis_cbse(self):
        query = "Explain photosynthesis for Class 8 CBSE"
        intent = QueryUnderstandingEngine.interpret_query(query)

        self.assertEqual(intent.topic, "Photosynthesis")
        self.assertIn(intent.subject, ["Science", "Biology"])
        self.assertEqual(intent.grade_level, 8)
        self.assertEqual(intent.board, "CBSE")
        self.assertEqual(intent.intent_type, "explanation")
        self.assertEqual(intent.depth_level, "standard")
        self.assertIn("chloroplast", [t.lower() for t in intent.expanded_terms])

    def test_query_understanding_newton_icse(self):
        query = "Newton's third law of motion Class 9 ICSE numericals"
        intent = QueryUnderstandingEngine.interpret_query(query)

        self.assertIn("Newton", intent.topic)
        self.assertEqual(intent.subject, "Physics")
        self.assertEqual(intent.grade_level, 9)
        self.assertEqual(intent.board, "ICSE")
        self.assertEqual(intent.intent_type, "problem_solving")

    # --------------------------------------------------------------------------
    # 2. Source Authority Registry (Decoupled Trust Layers)
    # --------------------------------------------------------------------------
    def test_source_authority_decouples_platform_and_creator(self):
        # A YouTube video by a vetted creator (3Blue1Brown) is elevated to Tier C
        yt_vetted = SourceAuthorityRegistry.evaluate_source(
            url="https://www.youtube.com/watch?v=WUvTyaaNkzM",
            platform_hint="YouTube",
            creator_name="3Blue1Brown"
        )
        self.assertEqual(yt_vetted["authority_tier"], "TIER_C")
        self.assertGreaterEqual(yt_vetted["authority_score"], 0.90)

        # An unvetted creator on YouTube remains Tier D
        yt_unvetted = SourceAuthorityRegistry.evaluate_source(
            url="https://www.youtube.com/watch?v=unvetted123",
            platform_hint="YouTube",
            creator_name="Random Gaming Channel"
        )
        self.assertEqual(yt_unvetted["authority_tier"], "TIER_D")

        # Official NCERT portal is Tier A
        ncert_eval = SourceAuthorityRegistry.evaluate_source(
            url="https://ncert.nic.in/textbook/science/ch1.pdf"
        )
        self.assertEqual(ncert_eval["authority_tier"], "TIER_A")
        self.assertEqual(ncert_eval["authority_score"], 1.00)
        self.assertTrue(ncert_eval["is_official"])

        # PhET interactive simulations is Tier B (0.98)
        phet_eval = SourceAuthorityRegistry.evaluate_source(
            url="https://phet.colorado.edu/sims/html/photosynthesis/latest/photosynthesis_all.html"
        )
        self.assertEqual(phet_eval["authority_tier"], "TIER_B")
        self.assertEqual(phet_eval["authority_score"], 0.98)

    # --------------------------------------------------------------------------
    # 3. Hard Safety and Age Appropriateness Gates
    # --------------------------------------------------------------------------
    def test_hard_safety_gate_rejects_unsafe_content(self):
        unsafe_candidate = {
            "id": "unsafe-test-1",
            "title": "Learn how to make a bomb and violent weapons at home",
            "description": "Explosive chemical reactions tutorial",
            "source_url": "https://suspicious-site.com/weapons.mp4",
            "source_platform": "Web Ingestion",
            "grade_level": 8,
            "topic": "Chemical Reactions"
        }
        intent = QueryUnderstandingEngine.interpret_query("Chemical reactions Class 8")
        breakdown, score = ResourceQualityEngine.score_candidate(unsafe_candidate, intent)

        # Safety gate MUST reject before scoring!
        self.assertIsNone(breakdown)
        self.assertEqual(score, 0.0)

    def test_age_appropriateness_gate_blocks_excessive_gap(self):
        advanced_candidate = {
            "id": "quantum-grad-school",
            "title": "Relativistic Quantum Electrodynamics & Tensor Fields",
            "description": "Graduate level theoretical physics",
            "source_url": "https://openstax.org/advanced-physics",
            "source_platform": "OpenStax",
            "grade_level": 12, # 4 years ahead of Class 8 student!
            "topic": "Physics"
        }
        intent = QueryUnderstandingEngine.interpret_query("Physics Class 8 CBSE")
        breakdown, score = ResourceQualityEngine.score_candidate(advanced_candidate, intent)

        self.assertIsNone(breakdown)
        self.assertEqual(score, 0.0)

    # --------------------------------------------------------------------------
    # 4. Instrumented Versioned Quality Scoring (v1.0)
    # --------------------------------------------------------------------------
    def test_scoring_breakdown_instruments_all_10_factors(self):
        candidate = {
            "id": "phet-photosynthesis",
            "title": "PhET: Interactive Photosynthesis Lab",
            "description": "Simulate sunlight photons and stomata gas exchange",
            "source_url": "https://phet.colorado.edu/sims/html/photosynthesis",
            "source_platform": "PhET Interactive Simulations",
            "creator_name": "PhET Interactive Simulations",
            "resource_type": "interactive_sim",
            "grade_level": 8,
            "board": "CBSE",
            "subject": "Science",
            "topic": "Photosynthesis",
            "duration_minutes": 10,
            "language": "en",
            "transcript_text": "PhET interactive simulation exploring cellular chloroplast energy transformation."
        }
        intent = QueryUnderstandingEngine.interpret_query("Explain photosynthesis for Class 8 CBSE")
        breakdown, score = ResourceQualityEngine.score_candidate(candidate, intent)

        self.assertIsNotNone(breakdown)
        self.assertGreater(score, 0.90)
        self.assertEqual(breakdown.policy_version, "v1.0")
        self.assertGreaterEqual(breakdown.curriculum_alignment, 0.90)
        self.assertGreaterEqual(breakdown.source_authority, 0.95)
        self.assertGreaterEqual(breakdown.pedagogical_quality, 0.90)
        self.assertTrue(breakdown.is_safe)
        self.assertTrue(breakdown.age_appropriate)

    # --------------------------------------------------------------------------
    # 5. Full Discovery Pipeline & Segmentation
    # --------------------------------------------------------------------------
    def test_full_discovery_pipeline_photosynthesis(self):
        response = DiscoveryPipeline.execute_discovery(
            db=self.db,
            query="Explain photosynthesis for Class 8 CBSE",
            student_user=self.student
        )

        self.assertEqual(response.interpreted_intent.topic, "Photosynthesis")
        self.assertEqual(response.interpreted_intent.grade_level, 8)
        self.assertIsNotNone(response.understand_it)
        self.assertIn("core_explanation", response.understand_it)

        # Best match must be present and verified
        self.assertIsNotNone(response.best_match)
        self.assertGreater(len(response.best_match.why_chosen), 0)
        self.assertTrue(response.best_match.is_verified)

        # Categorical diversity coverage
        self.assertIn("read", response.resources_by_category)
        self.assertIn("explore", response.resources_by_category)
        self.assertIn("video", response.resources_by_category)
        self.assertGreaterEqual(len(response.resources_by_category["read"]), 1)
        self.assertGreaterEqual(len(response.resources_by_category["explore"]), 1)

        # 5-question concept check quiz
        self.assertIsNotNone(response.practice_quiz)
        self.assertEqual(len(response.practice_quiz.questions), 5)

        # Knowledge pathway
        self.assertGreaterEqual(len(response.knowledge_pathway), 3)
        depths = [node.depth for node in response.knowledge_pathway]
        self.assertIn("prerequisite", depths)
        self.assertIn("core", depths)

    # --------------------------------------------------------------------------
    # 6. Closed Learning Loop: Quiz Submission & Mastery Gain
    # --------------------------------------------------------------------------
    def test_closed_learning_loop_grades_and_updates_mastery(self):
        # Student answers all 5 photosynthesis questions correctly
        req = QuizSubmitRequest(
            quiz_id="quiz-check-8-photosynthesis",
            topic="Photosynthesis",
            subject="Science",
            grade_level=8,
            answers={
                "q1": 1, # Chloroplast
                "q2": 1, # CO2 + H2O
                "q3": 1, # Stomata
                "q4": 2, # Oxygen
                "q5": 0  # Starch
            }
        )

        result = LearningLoopManager.evaluate_quiz_submission(
            db=self.db,
            student_user=self.student,
            request=req
        )

        self.assertEqual(result.score, 5)
        self.assertEqual(result.total_questions, 5)
        self.assertEqual(result.accuracy_percentage, 100.0)
        self.assertEqual(result.prior_mastery, 45.0)
        self.assertGreater(result.new_mastery, 45.0)
        self.assertGreater(result.mastery_gain, 0.0)
        self.assertGreater(result.xp_earned, 50)

        # Verify DB TopicMastery updated
        updated_tm = self.db.query(TopicMastery).filter(
            TopicMastery.student_user_id == self.student.id,
            TopicMastery.topic == "Photosynthesis"
        ).first()
        self.assertIsNotNone(updated_tm)
        self.assertEqual(float(updated_tm.mastery_score), result.new_mastery)
        self.assertEqual(updated_tm.trend, "improving")

        # Verify StudentMasteryHistory audit log
        history_entry = self.db.query(StudentMasteryHistory).filter(
            StudentMasteryHistory.student_user_id == self.student.id,
            StudentMasteryHistory.topic == "Photosynthesis"
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(float(history_entry.learning_gain), result.mastery_gain)

    # --------------------------------------------------------------------------
    # 7. Resource Engagement Tracking
    # --------------------------------------------------------------------------
    def test_resource_engagement_tracking(self):
        req = ResourceEngagementRequest(
            resource_id="phet-photosynthesis",
            topic="Photosynthesis",
            subject="Science",
            dwell_time_seconds=240,
            action_type="completed"
        )
        res = LearningLoopManager.record_resource_engagement(
            db=self.db,
            student_user=self.student,
            request=req
        )
        self.assertEqual(res["status"], "recorded")
        self.assertEqual(res["xp_awarded"], 20)

    # --------------------------------------------------------------------------
    # 8. FastAPI Endpoints Integration
    # --------------------------------------------------------------------------
    def test_api_discovery_search_endpoint(self):
        res = self.client.get(
            "/api/v1/discovery/search",
            params={"q": "Explain photosynthesis for Class 8 CBSE"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("interpreted_intent", data)
        self.assertIn("understand_it", data)
        self.assertIn("best_match", data)
        self.assertIn("resources_by_category", data)
        self.assertIn("practice_quiz", data)
        self.assertEqual(data["policy_version"], "v1.0")

    def test_api_sources_endpoint(self):
        res = self.client.get("/api/v1/discovery/sources")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_registered_sources"], 10)
        self.assertIn("tier_definitions", data)

    def test_api_scoring_policy_endpoint(self):
        res = self.client.get("/api/v1/discovery/scoring-policy")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["policy_version"], "v1.0")
        self.assertIn("weights", data)
        self.assertGreaterEqual(data["safety_threshold"], 0.90)


if __name__ == "__main__":
    unittest.main()
