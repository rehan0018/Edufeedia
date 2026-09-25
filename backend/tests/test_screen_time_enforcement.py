"""
Comprehensive Test Suite for Parental Screen-Time Policy Enforcement,
Bedtime Curfew Gating, and Authoritative Heartbeat Telemetry.
"""

import unittest
import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.models import (
    User, ParentalScreenTimePolicy, LearningEvent, UserInteraction, ContentItem
)
from app.core.screen_time_enforcer import ScreenTimePolicyEnforcer

client = TestClient(app)

class TestScreenTimeEnforcement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Authenticate as student (Rahul)
        s_res = client.post("/api/v1/auth/login", json={
            "email": "rahul@apexschool.edu",
            "password": "Student123!"
        })
        assert s_res.status_code == 200, f"Login failed: {s_res.text}"
        cls.student_token = s_res.json()["access_token"]
        cls.student_id = s_res.json()["user_id"]
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    def setUp(self):
        self.db = SessionLocal()
        self.content_item = self.db.query(ContentItem).first()
        if not self.content_item:
            self.content_item = ContentItem(
                id="ci-test-enforce",
                title="Laws of Motion",
                subject="Physics",
                topic="Newtonian Mechanics",
                is_approved=True,
                duration_minutes=15
            )
            self.db.add(self.content_item)
            self.db.commit()

        # Clean up any transient learning events or policies for Rahul
        self.db.query(LearningEvent).filter(LearningEvent.student_user_id == self.student_id).delete()
        self.db.query(UserInteraction).filter(UserInteraction.user_id == self.student_id).delete()
        self.db.query(ParentalScreenTimePolicy).filter(ParentalScreenTimePolicy.student_user_id == self.student_id).delete()
        self.db.commit()

    def tearDown(self):
        self.db.query(LearningEvent).filter(LearningEvent.student_user_id == self.student_id).delete()
        self.db.query(UserInteraction).filter(UserInteraction.user_id == self.student_id).delete()
        self.db.query(ParentalScreenTimePolicy).filter(ParentalScreenTimePolicy.student_user_id == self.student_id).delete()
        self.db.commit()
        self.db.close()

    def test_01_screen_time_status_endpoint(self):
        """Student can retrieve active screen-time limits and live status."""
        res = client.get("/api/v1/students/screen-time-status", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("today_minutes", data)
        self.assertIn("daily_limit_minutes", data)
        self.assertIn("remaining_minutes", data)
        self.assertIn("is_locked", data)
        self.assertEqual(data["today_minutes"], 0)

    def test_02_heartbeat_telemetry_recording(self):
        """Sending active heartbeat pings records genuine LearningEvent logs without fake estimates."""
        # Ping 1: 30 seconds
        res1 = client.post(
            "/api/v1/students/heartbeat",
            headers=self.student_headers,
            json={"active_seconds": 30, "activity_type": "reading"}
        )
        self.assertEqual(res1.status_code, 200)

        # Ping 2: 60 seconds
        res2 = client.post(
            "/api/v1/students/heartbeat",
            headers=self.student_headers,
            json={"active_seconds": 60, "activity_type": "video"}
        )
        self.assertEqual(res2.status_code, 200)

        # Verify LearningEvents in DB
        events = self.db.query(LearningEvent).filter(
            LearningEvent.student_user_id == self.student_id,
            LearningEvent.event_type == "heartbeat"
        ).all()
        self.assertEqual(len(events), 2)
        total_logged = sum(e.verified_seconds for e in events)
        self.assertEqual(total_logged, 90)

        # Screen time should be 1 minute (90s / 60)
        status_res = client.get("/api/v1/students/screen-time-status", headers=self.student_headers)
        self.assertEqual(status_res.json()["today_minutes"], 1)

    def test_03_bedtime_curfew_server_side_enforcement(self):
        """When curfew is active, student endpoints return HTTP 423 (Locked)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        # Create policy where curfew spans current time (1 hour ago to 1 hour ahead)
        start_hour = (now - datetime.timedelta(hours=1)).strftime("%H:%M")
        end_hour = (now + datetime.timedelta(hours=1)).strftime("%H:%M")

        policy = ParentalScreenTimePolicy(
            parent_user_id=self.student_id,
            student_user_id=self.student_id,
            daily_limit_minutes=90,
            curfew_start_time=start_hour,
            curfew_end_time=end_hour,
            curfew_enabled=True,
            ai_tutor_max_daily_minutes=30
        )
        self.db.add(policy)
        self.db.commit()

        # 1. Screen time status reflects locked
        status_res = client.get("/api/v1/students/screen-time-status", headers=self.student_headers)
        self.assertTrue(status_res.json()["is_curfew_active"])
        self.assertTrue(status_res.json()["is_locked"])
        self.assertEqual(status_res.json()["lock_reason"], "curfew")

        # 2. Activity registration is locked
        act_res = client.post("/api/v1/students/activity", headers=self.student_headers)
        self.assertEqual(act_res.status_code, 423)
        self.assertIn("curfew", act_res.json()["detail"].lower())

    def test_04_daily_limit_server_side_enforcement(self):
        """When daily screen-time limit is reached, student endpoints return HTTP 423."""
        # Set limit to 10 minutes
        policy = ParentalScreenTimePolicy(
            parent_user_id=self.student_id,
            student_user_id=self.student_id,
            daily_limit_minutes=10,
            curfew_start_time="03:00",
            curfew_end_time="04:00",
            curfew_enabled=False,
            ai_tutor_max_daily_minutes=30
        )
        self.db.add(policy)
        self.db.commit()

        # Log 15 minutes of verified learning events
        event = LearningEvent(
            student_user_id=self.student_id,
            content_item_id=self.content_item.id,
            event_type="heartbeat",
            verified_seconds=15 * 60
        )
        self.db.add(event)
        self.db.commit()

        # Status reflects over limit
        status_res = client.get("/api/v1/students/screen-time-status", headers=self.student_headers)
        self.assertTrue(status_res.json()["is_over_limit"])
        self.assertTrue(status_res.json()["is_locked"])
        self.assertEqual(status_res.json()["lock_reason"], "daily_limit")

        # Progress update is locked with HTTP 423
        prog_res = client.post(
            "/api/v1/content/progress",
            headers=self.student_headers,
            json={"content_item_id": self.content_item.id, "progress_percentage": 50}
        )
        self.assertEqual(prog_res.status_code, 423)
        self.assertIn("daily screen time limit reached", prog_res.json()["detail"].lower())

    def test_05_ai_tutor_quota_enforcement(self):
        """When student exceeds parent AI tutor limit, /tutor/ask returns HTTP 423."""
        policy = ParentalScreenTimePolicy(
            parent_user_id=self.student_id,
            student_user_id=self.student_id,
            daily_limit_minutes=120,
            curfew_enabled=False,
            ai_tutor_max_daily_minutes=3  # 3 minutes = 1 query
        )
        self.db.add(policy)
        self.db.commit()

        # Log 1 prior AI interaction (3 minutes used)
        interaction = UserInteraction(
            user_id=self.student_id,
            content_item_id=self.content_item.id,
            interaction_type="ai_query",
            dwell_time_seconds=180
        )
        self.db.add(interaction)
        self.db.commit()

        # Call /tutor/ask
        tutor_res = client.post(
            "/api/v1/tutor/ask",
            headers=self.student_headers,
            json={"question": "Can you explain Newton's second law?"}
        )
        self.assertEqual(tutor_res.status_code, 423)
        self.assertIn("ai tutoring limit reached", tutor_res.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
