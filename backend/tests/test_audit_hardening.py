"""
Unit & Regression Test Suite for Production Hardening & Audit Verification.
Validates:
1. Parent PIN Gate: Strictly fails-closed in production (no 1234/0000 bypass)
2. Scalable Candidate Retrieval: SQL-level filtering with bounds (no ContentItem.all())
3. Dynamic Educational Context: YouTube subject inference (e.g. quadratic equations -> Mathematics, not Science)
4. Telemetry Integrity: Server-authoritative dwell time with anti-replay rate bounding
5. Truthful Provenance: Unverified candidates have verified_at=None and verification_status='pending_verification'
"""

import sys
import unittest
import datetime
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.config import settings
from app.models.models import User, ContentItem, LearningEvent
from app.discovery.query_understanding import QueryUnderstandingEngine
from app.discovery.candidate_builder import CandidateBuilder
from app.discovery.youtube_search import YouTubeDiscoveryAdapter, infer_video_educational_context
from app.discovery.provenance import ProvenanceGenerator
from app.discovery.learning_loop import LearningLoopManager
from app.schemas.schemas import InterpretedIntent, ResourceEngagementRequest
from app.core.security import get_password_hash, create_access_token


class TestAuditHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

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
        # Seed test parent
        self.parent = User(
            id="parent-audit-test",
            email="auditparent@edufeedia.com",
            first_name="Parent",
            last_name="Auditor",
            role="parent",
            account_status="ACTIVE",
            parent_pin_hash=None  # Unconfigured PIN
        )
        self.db.merge(self.parent)

        # Seed test student
        self.student = User(
            id="student-audit-test",
            email="auditstudent@edufeedia.com",
            first_name="Student",
            last_name="Auditor",
            role="student",
            account_status="ACTIVE"
        )
        self.db.merge(self.student)
        self.db.commit()

        token = create_access_token({"sub": self.parent.email, "role": "parent", "id": self.parent.id})
        self.parent_headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.db.close()

    def test_01_parent_pin_production_fail_closed(self):
        """Security P0: When in production and no PIN is configured, verify-pin MUST fail closed."""
        original_env = settings.ENVIRONMENT
        original_demo = getattr(settings, "DEMO_MODE", False)

        try:
            # Simulate production
            settings.ENVIRONMENT = "production"
            settings.DEMO_MODE = False

            # Try common default PINs '1234' and '0000'
            for bad_pin in ["1234", "0000", "9999"]:
                res = self.client.post(
                    "/api/v1/parents/verify-pin",
                    headers=self.parent_headers,
                    json={"pin": bad_pin}
                )
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertFalse(data["verified"])
                self.assertIn("not configured", data["message"])
        finally:
            settings.ENVIRONMENT = original_env
            settings.DEMO_MODE = original_demo

    def test_02_dynamic_youtube_subject_and_grade_inference(self):
        """Content Intelligence: Dynamically infers Mathematics, Physics, Chemistry, Biology and Class."""
        # Math query
        math_ctx = infer_video_educational_context(
            title="Solving Quadratic Equations by Factoring - Class 10",
            description="Learn how to solve quadratic equations step by step using standard algebraic techniques.",
            default_topic="Quadratic Equations",
            requested_subject="Science",  # Even if requested generally as Science
            requested_board="CBSE",
            requested_grade=10
        )
        self.assertEqual(math_ctx["subject"], "Mathematics")
        self.assertEqual(math_ctx["grade_level"], 10)

        # Physics query
        phy_ctx = infer_video_educational_context(
            title="Newton's Laws of Motion and Impulse - Class 9 ICSE",
            description="Action reaction pairs, inertia, and force equations.",
            default_topic="Newton's Laws",
            requested_subject=None,
            requested_board=None,
            requested_grade=8
        )
        self.assertEqual(phy_ctx["subject"], "Physics")
        self.assertEqual(phy_ctx["board"], "ICSE")
        self.assertEqual(phy_ctx["grade_level"], 9)

        # Biology query
        bio_ctx = infer_video_educational_context(
            title="Photosynthesis and Chloroplast Function in Plant Nutrition",
            description="How chlorophyll absorbs light to convert carbon dioxide into glucose.",
            default_topic="Photosynthesis",
            requested_subject="Science",
            requested_board="CBSE",
            requested_grade=8
        )
        self.assertEqual(bio_ctx["subject"], "Biology")

    def test_03_youtube_transcript_truthfulness(self):
        """Content Intelligence: Video descriptions are not misrepresented as transcripts."""
        from unittest.mock import patch, MagicMock

        mock_search_res = MagicMock()
        mock_search_res.status_code = 200
        mock_search_res.json.return_value = {
            "items": [{
                "id": {"videoId": "test1234"},
                "snippet": {
                    "title": "Quadratic Formula Masterclass",
                    "description": "Video description text describing the formula.",
                    "channelTitle": "Math Studio",
                    "channelId": "UC12345"
                }
            }]
        }
        with patch("os.getenv", return_value="test_live_key_xyz"), \
             patch("requests.get", return_value=mock_search_res):
            candidates = YouTubeDiscoveryAdapter.search_candidates(
                query="quadratic equations",
                topic="Quadratic Equations",
                grade_level=10,
                language="en",
                subject="Mathematics",
                max_results=5
            )
            self.assertGreater(len(candidates), 0)
            cand = candidates[0]
            # Description must remain description, NOT transcript_summary
            self.assertEqual(cand["description"], "Video description text describing the formula.")
            self.assertIsNone(cand.get("transcript_summary"))
            self.assertEqual(cand["subject"], "Mathematics")

    def test_04_server_authoritative_dwell_time_anti_replay(self):
        """Telemetry Integrity P0: Fast replay attacks (<2 sec apart) are clamped to 0 verified seconds."""
        db = self.SessionLocal()
        student = db.query(User).filter(User.id == "student-audit-test").first()

        req1 = ResourceEngagementRequest(
            resource_id="res-math-1",
            topic="Quadratic Equations",
            subject="Mathematics",
            dwell_time_seconds=60,
            action_type="viewed"
        )
        res1 = LearningLoopManager.record_resource_engagement(db, student, req1)
        self.assertEqual(res1["dwell_time_seconds"], 60)

        # Immediate replay submission claiming 180 seconds only milliseconds later
        req2 = ResourceEngagementRequest(
            resource_id="res-math-1",
            topic="Quadratic Equations",
            subject="Mathematics",
            dwell_time_seconds=180,
            action_type="viewed"
        )
        res2 = LearningLoopManager.record_resource_engagement(db, student, req2)
        # Server must clamp to 0 because elapsed physical time was ~0 seconds
        self.assertEqual(res2["dwell_time_seconds"], 0)
        db.close()

    def test_05_truthful_provenance_records(self):
        """Provenance Integrity: Unverified candidates have verified_at=None and verification_status='pending_verification'."""
        candidate = {
            "source_name": "Open Community Tutor",
            "source_platform": "YouTube",
            "title": "Quadratic formula solved easily",
            "topic": "Quadratic Equations",
            "grade_level": 10,
            "board": "CBSE",
            "subject": "Mathematics",
            "authority_tier": "TIER_C",
            "is_verified": False,
            "verified_at": None,
            "origin": "youtube"
        }
        intent = InterpretedIntent(
            subject="Mathematics",
            topic="Quadratic Equations",
            grade_level=10,
            board="CBSE",
            intent_type="explanation",
            depth_level="standard",
            format_preference="all",
            language="en",
            expanded_terms=[]
        )

        evidence = ProvenanceGenerator.generate_provenance_evidence(candidate, intent)
        # Must NOT be the old fabricated "2026-01-15T00:00:00Z"
        self.assertIsNone(evidence["verified_at"])
        self.assertEqual(evidence["verification_status"], "pending_verification")
        self.assertIn("Inferred from creator", evidence["curriculum_alignment"]["evidence"])

    def test_06_candidate_builder_sql_bounded(self):
        """Performance P0: Candidate pool builds via SQL-filtered bounded query."""
        db = self.SessionLocal()
        # Seed 5 items
        for i in range(5):
            it = ContentItem(
                id=f"audit-item-{i}",
                title=f"Lesson on Quadratic Equations #{i}",
                topic="Quadratic Equations",
                subject="Mathematics",
                grade_level=10,
                board="CBSE",
                duration_minutes=8,
                is_approved=True,
                source_url=f"https://edufeedia.com/audit-{i}",
                source_platform="Edufeedia Studio",
                type="video"
            )
            db.merge(it)
        db.commit()

        intent = InterpretedIntent(
            subject="Mathematics",
            topic="Quadratic Equations",
            grade_level=10,
            board="CBSE",
            intent_type="explanation",
            depth_level="standard",
            format_preference="all",
            language="en",
            expanded_terms=["quadratic", "roots", "algebra"]
        )
        pool = CandidateBuilder.build_candidate_pool(db, intent, max_total_candidates=15)
        self.assertGreater(len(pool), 0)
        self.assertLessEqual(len(pool), 15)
        db.close()


if __name__ == "__main__":
    unittest.main()
