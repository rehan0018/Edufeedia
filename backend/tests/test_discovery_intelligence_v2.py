"""
Unit and Integration Tests for Discovery Intelligence v2:
- YouTube Transcript Acquisition & TimedText XML parsing
- Spoken Content Understanding & Pedagogical Depth Classification
- Spoken Safety Audit via MultilingualSafetyEngine
- Session Lifecycle: /session/start -> /session/heartbeat -> /session/end
- Server-authoritative dwell time enforcement & concurrency isolation
- Pre/Post Assessment with Hake's Normalized Learning Gain calculation
- Offline storage in EmpiricalLearningGainRecord without premature ranking contamination
- FastAPI endpoints validation
"""

import sys
import unittest
import datetime
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

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
    StudentMasteryHistory, LearningEvent, RewardLedger, EmpiricalLearningGainRecord
)
from app.discovery.youtube_transcript import YouTubeTranscriptAcquirer, ContentUnderstandingEngine
from app.discovery.learning_loop import LearningLoopManager
from app.schemas.schemas import (
    SessionStartRequest, SessionHeartbeatRequest, SessionEndRequest,
    PrePostAssessmentSubmitRequest
)
from app.routers.auth import get_current_user


class TestDiscoveryIntelligenceV2(unittest.TestCase):
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

        cls.mock_student = User(
            id="student-intel-v2",
            email="intel_student@edufeedia.test",
            first_name="Intelligence",
            last_name="Student",
            role="student",
            is_verified=True,
            email_verified=True,
            account_status="ACTIVE",
            token_version=1
        )
        cls.mock_profile = StudentProfile(
            user_id="student-intel-v2",
            grade_level=8,
            board="CBSE",
            learning_preference=["video", "simulation"],
            xp_score=500
        )
        cls.mock_student.student_profile = cls.mock_profile

        def override_get_current_user():
            return cls.mock_student

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Seed test student if not present
        if not self.db.query(User).filter_by(id="student-intel-v2").first():
            student = User(
                id="student-intel-v2",
                email="intel_student@edufeedia.test",
                first_name="Intelligence",
                last_name="Student",
                role="student",
                is_verified=True,
                email_verified=True,
                account_status="ACTIVE",
                token_version=1
            )
            self.db.add(student)
            profile = StudentProfile(
                user_id="student-intel-v2",
                grade_level=8,
                board="CBSE",
                learning_preference=["video", "simulation"],
                xp_score=500
            )
            self.db.add(profile)
            self.db.commit()

    def tearDown(self):
        self.db.close()

    # =========================================================================
    # 1. YouTube Transcript Acquisition Tests
    # =========================================================================

    def test_transcript_invalid_video_id(self):
        """Invalid or too short video IDs fail fast without network requests."""
        res = YouTubeTranscriptAcquirer.fetch_transcript("")
        self.assertFalse(res["has_transcript"])
        self.assertEqual(res["error"], "Invalid video ID format")

        res_short = YouTubeTranscriptAcquirer.fetch_transcript("123")
        self.assertFalse(res_short["has_transcript"])

    @patch("requests.get")
    def test_transcript_page_fetch_failure(self, mock_get):
        """HTTP error on YouTube page returns clean structured error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        res = YouTubeTranscriptAcquirer.fetch_transcript("valid_id_123")
        self.assertFalse(res["has_transcript"])
        self.assertIn("404", res["error"])

    @patch("requests.get")
    def test_transcript_successful_timedtext_extraction(self, mock_get):
        """Authentic YouTube page with caption tracks and timedtext XML returns parsed segments."""
        # 1. Page response with player captions manifest
        page_html = """
        <html><body>
        <script>
        var ytInitialPlayerResponse = {
            "captions": {
                "playerCaptionsTracklistRenderer": {
                    "captionTracks": [
                        {
                            "baseUrl": "https://www.youtube.com/api/timedtext?v=test",
                            "languageCode": "en",
                            "name": {"simpleText": "English"},
                            "kind": "standard"
                        }
                    ]
                }
            }
        };
        </script>
        </body></html>
        """

        # 2. TimedText XML response
        timedtext_xml = """<?xml version="1.0" encoding="utf-8" ?>
        <transcript>
            <text start="0.5" dur="3.2">Hello and welcome to photosynthesis &amp; cellular energy.</text>
            <text start="3.8" dur="4.1">Today we will examine chloroplasts and chlorophyll &#39;a&#39; absorption.</text>
        </transcript>
        """

        def mock_get_side_effect(url, *args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            if "watch?v=" in url:
                resp.text = page_html
            elif "timedtext" in url:
                resp.text = timedtext_xml
            return resp

        mock_get.side_effect = mock_get_side_effect

        res = YouTubeTranscriptAcquirer.fetch_transcript("photo12345")
        self.assertTrue(res["has_transcript"])
        self.assertEqual(len(res["segments"]), 2)
        self.assertEqual(res["segments"][0]["text"], "Hello and welcome to photosynthesis & cellular energy.")
        self.assertEqual(res["segments"][1]["text"], "Today we will examine chloroplasts and chlorophyll 'a' absorption.")
        self.assertIn("chloroplasts", res["full_text"])
        self.assertEqual(res["provenance"], "youtube_timedtext_v3")

    # =========================================================================
    # 2. Spoken Content Understanding & Safety Tests
    # =========================================================================

    def test_content_understanding_empty_fallback(self):
        """Short or empty transcripts produce clean fallback with default grade."""
        analysis = ContentUnderstandingEngine.analyze_content("", topic="Gravity", grade_level=9)
        self.assertEqual(analysis["pedagogical_depth"], "standard")
        self.assertIn("Gravity", analysis["concepts_detected"])
        self.assertEqual(analysis["reading_grade_level"], 9)
        self.assertEqual(analysis["word_count"], 0)

    def test_content_understanding_depth_and_concept_extraction(self):
        """Extracts repeated concepts, detects depth markers, and synthesizes diagnostic question."""
        lecture_transcript = (
            "Welcome to this lecture on thermodynamics and energy conservation. "
            "In thermodynamics, heat and work represent energy transfer across boundaries. "
            "We derive the first law differential equation and prove the theorem of entropy conservation. "
            "Thermodynamics governs chemical reactions and equilibrium states in physical chemistry. "
            "Let us examine this hypothesis and thermodynamic proof in detail with mathematical rigor. "
        ) * 4  # Repeat to build realistic word count

        analysis = ContentUnderstandingEngine.analyze_content(
            transcript_text=lecture_transcript,
            topic="Thermodynamics",
            subject="Physics",
            grade_level=11
        )

        self.assertIn("Thermodynamics", analysis["concepts_detected"])
        self.assertEqual(analysis["pedagogical_depth"], "advanced")
        self.assertTrue(analysis["safety_audit"]["is_safe"])
        self.assertEqual(len(analysis["learning_outcomes"]), 3)
        self.assertGreater(len(analysis["diagnostic_questions"]), 0)
        diag = analysis["diagnostic_questions"][0]
        self.assertIn("Thermodynamics", diag.question_text)
        self.assertEqual(diag.correct_option_index, 0)

    def test_content_understanding_introductory_depth(self):
        """Detects beginner/introductory vocabulary markers."""
        intro_transcript = (
            "This is a simple introduction to basic magnets. "
            "Imagine you have two easy magnets. Picture this in your everyday life. "
            "We start with the beginner basics of north and south poles. "
        ) * 3

        analysis = ContentUnderstandingEngine.analyze_content(
            transcript_text=intro_transcript,
            topic="Magnets",
            subject="Physics",
            grade_level=6
        )
        self.assertEqual(analysis["pedagogical_depth"], "introductory")

    # =========================================================================
    # 3. Session Lifecycle & Concurrency Isolation Tests
    # =========================================================================

    def test_session_lifecycle_start_heartbeat_end(self):
        """Tests end-to-end session start, heartbeat clamping, and completion XP award."""
        # 1. Start Session
        start_req = SessionStartRequest(
            resource_id="res_optics_101",
            topic="Ray Optics",
            subject="Physics",
            grade_level=10
        )
        start_res = LearningLoopManager.start_learning_session(self.mock_student, start_req)
        self.assertTrue(start_res.session_id.startswith("sess_"))
        self.assertEqual(start_res.status, "active")

        # 2. Heartbeat (simulate client sending dwell time with server elapsed pacing)
        session_key = f"{self.mock_student.id}:{start_res.session_id}"
        # Set last_heartbeat_at to 45 seconds in the past to allow dwell verification
        past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=45)
        LearningLoopManager._ACTIVE_SESSIONS[session_key]["last_heartbeat_at"] = past_time

        hb_req = SessionHeartbeatRequest(
            session_id=start_res.session_id,
            resource_id="res_optics_101",
            dwell_seconds=30,
            is_active=True
        )
        hb_res = LearningLoopManager.heartbeat_learning_session(self.db, self.mock_student, hb_req)
        self.assertEqual(hb_res.verified_seconds, 30)
        self.assertEqual(hb_res.session_accumulated_seconds, 30)

        # 3. Conclude Session
        end_req = SessionEndRequest(
            session_id=start_res.session_id,
            resource_id="res_optics_101",
            completed=True
        )
        end_res = LearningLoopManager.end_learning_session(self.db, self.mock_student, end_req)
        self.assertEqual(end_res.status, "completed")
        self.assertEqual(end_res.total_verified_seconds, 30)
        self.assertEqual(end_res.xp_awarded, 25)

    def test_session_concurrency_isolation(self):
        """
        Validates telemetry key: student_id + session_id
        Concurrent learning sessions on different resources must maintain independent accumulated seconds.
        """
        # Session A: Math
        start_a = LearningLoopManager.start_learning_session(
            self.mock_student,
            SessionStartRequest(resource_id="math_algebra_1", topic="Algebra", subject="Mathematics")
        )

        # Session B: Science
        start_b = LearningLoopManager.start_learning_session(
            self.mock_student,
            SessionStartRequest(resource_id="science_cells_2", topic="Cells", subject="Biology")
        )

        self.assertNotEqual(start_a.session_id, start_b.session_id)

        # Advance server clock for Session A only
        key_a = f"{self.mock_student.id}:{start_a.session_id}"
        LearningLoopManager._ACTIVE_SESSIONS[key_a]["last_heartbeat_at"] = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=60)
        )

        LearningLoopManager.heartbeat_learning_session(
            self.db, self.mock_student,
            SessionHeartbeatRequest(session_id=start_a.session_id, resource_id="math_algebra_1", dwell_seconds=50)
        )

        # Verify Session A has 50 accumulated seconds, while Session B remains at 0
        sess_a = LearningLoopManager._ACTIVE_SESSIONS[key_a]
        key_b = f"{self.mock_student.id}:{start_b.session_id}"
        sess_b = LearningLoopManager._ACTIVE_SESSIONS[key_b]

        self.assertEqual(sess_a["accumulated_seconds"], 50)
        self.assertEqual(sess_b["accumulated_seconds"], 0)

    # =========================================================================
    # 4. Empirical Learning Gain & Offline Storage Tests
    # =========================================================================

    def test_pre_post_assessment_and_hakes_normalized_gain(self):
        """
        Verifies Hake's normalized gain calculation:
        g = (post - pre) / (100 - pre)
        Pre = 40%, Post = 85% -> g = (85 - 40) / (100 - 40) = 45 / 60 = 0.75 (High gain)
        Persisted offline in EmpiricalLearningGainRecord without contaminating live ranking.
        """
        with patch("app.discovery.pipeline.DiscoveryPipeline.generate_concept_check") as mock_quiz:
            # Mock 2-question quiz
            mock_quiz.return_value = MagicMock(
                questions=[
                    MagicMock(id="q1", correct_option_index=0),
                    MagicMock(id="q2", correct_option_index=1),
                ]
            )

            # Submit Post-test with both correct answers (100%) against pre-test of 20%
            assessment_req = PrePostAssessmentSubmitRequest(
                resource_id="res_kinematics_5",
                session_id="sess_kine_99",
                topic="Kinematics",
                subject="Physics",
                grade_level=9,
                assessment_stage="post_test",
                pre_test_score_pct=20.0,
                answers={"q1": 0, "q2": 1}
            )

            gain_result = LearningLoopManager.evaluate_pre_post_assessment(
                self.db, self.mock_student, assessment_req
            )

            self.assertEqual(gain_result.pre_test_score_pct, 20.0)
            self.assertEqual(gain_result.post_test_score_pct, 100.0)
            self.assertEqual(gain_result.raw_gain_pct, 80.0)
            # Normalized gain g = 80 / (100 - 20) = 80 / 80 = 1.0000
            self.assertEqual(gain_result.normalized_gain, 1.0)
            self.assertIn("High normalized learning gain", gain_result.interpretation)

            # Verify persisted offline in database
            db_record = self.db.query(EmpiricalLearningGainRecord).filter_by(
                resource_id="res_kinematics_5",
                student_user_id=self.mock_student.id
            ).first()
            self.assertIsNotNone(db_record)
            self.assertEqual(db_record.normalized_gain, 1.0)
            self.assertEqual(db_record.session_id, "sess_kine_99")

    # =========================================================================
    # 5. FastAPI Endpoints Integration Tests
    # =========================================================================

    def test_api_session_lifecycle(self):
        """API endpoints: /session/start, /session/heartbeat, and /session/end succeed."""
        start_payload = {
            "resource_id": "api_res_chemistry_3",
            "topic": "Chemical Bonding",
            "subject": "Chemistry",
            "grade_level": 10
        }
        res_start = self.client.post("/api/v1/discovery/session/start", json=start_payload)
        self.assertEqual(res_start.status_code, 200)
        sess_data = res_start.json()
        session_id = sess_data["session_id"]
        self.assertTrue(session_id.startswith("sess_"))

        # Heartbeat
        hb_payload = {
            "session_id": session_id,
            "resource_id": "api_res_chemistry_3",
            "dwell_seconds": 15,
            "is_active": True
        }
        res_hb = self.client.post("/api/v1/discovery/session/heartbeat", json=hb_payload)
        self.assertEqual(res_hb.status_code, 200)
        self.assertEqual(res_hb.json()["session_id"], session_id)

        # End session
        end_payload = {
            "session_id": session_id,
            "resource_id": "api_res_chemistry_3",
            "completed": True
        }
        res_end = self.client.post("/api/v1/discovery/session/end", json=end_payload)
        self.assertEqual(res_end.status_code, 200)
        self.assertEqual(res_end.json()["status"], "completed")

    @patch("app.discovery.youtube_transcript.YouTubeTranscriptAcquirer.fetch_transcript")
    def test_api_transcript_inspection(self, mock_fetch):
        """GET /api/v1/discovery/transcript/{video_id} returns content analysis."""
        mock_fetch.return_value = {
            "has_transcript": True,
            "video_id": "test_video_123",
            "full_text": "In this lesson on plant cells we observe chloroplasts and cellular cell walls under microscopes.",
            "segments": [{"start": 0.0, "duration": 5.0, "text": "In this lesson on plant cells..."}],
            "language": "en",
            "provenance": "youtube_timedtext_v3"
        }

        res = self.client.get("/api/v1/discovery/transcript/test_video_123?topic=Plant%20Cells&subject=Biology&grade=8")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["has_transcript"])
        self.assertEqual(data["video_id"], "test_video_123")
        self.assertIn("content_analysis", data)
        self.assertIn("concepts_detected", data["content_analysis"])


if __name__ == "__main__":
    unittest.main()
