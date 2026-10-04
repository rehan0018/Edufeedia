import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)

class TestEdufeediaKidsAndParentHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.seed_kids_data import seed_kids_ecosystem
        seed_kids_ecosystem()

        # 1. Login as parent
        p_res = client.post("/api/v1/auth/login", json={
            "email": "parent@gmail.com",
            "password": "Parent123!"
        })
        assert p_res.status_code == 200, f"Parent login failed: {p_res.text}"
        cls.parent_token = p_res.json()["access_token"]
        cls.parent_headers = {"Authorization": f"Bearer {cls.parent_token}"}

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_parent_pin_setup_and_verification(self):
        # Set PIN to 1234
        pin_res = client.post(
            "/api/v1/parents/pin",
            headers=self.parent_headers,
            json={"pin": "1234"}
        )
        self.assertEqual(pin_res.status_code, 200)
        self.assertEqual(pin_res.json()["status"], "success")

        # Verify correct PIN
        verify_res = client.post(
            "/api/v1/parents/verify-pin",
            headers=self.parent_headers,
            json={"pin": "1234"}
        )
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.json()["verified"])

        # Verify incorrect PIN fails
        verify_bad = client.post(
            "/api/v1/parents/verify-pin",
            headers=self.parent_headers,
            json={"pin": "9999"}
        )
        self.assertEqual(verify_bad.status_code, 200)
        self.assertFalse(verify_bad.json()["verified"])

    def test_02_child_profile_crud_and_controls(self):
        # List children
        list_res = client.get("/api/v1/parents/children", headers=self.parent_headers)
        self.assertEqual(list_res.status_code, 200)
        data = list_res.json()
        children_list = data if isinstance(data, list) else data.get("children", [])
        self.assertGreaterEqual(len(children_list), 1)

        # Create a new child profile
        create_res = client.post(
            "/api/v1/parents/children",
            headers=self.parent_headers,
            json={
                "name": "Rohan",
                "age": 6,
                "avatar_mascot": "lion",
                "preferred_language": "en",
                "interests": ["STEM", "Creativity"],
                "daily_limit_minutes": 40
            }
        )
        self.assertIn(create_res.status_code, [200, 201])
        new_child = create_res.json()
        child_id = new_child["id"]
        self.assertEqual(new_child["name"], "Rohan")
        self.assertEqual(new_child["age"], 6)

        # Update child controls (Categories & Preferences)
        ctrl_res = client.put(
            f"/api/v1/parents/children/{child_id}/controls",
            headers=self.parent_headers,
            json={
                "allowed_categories": ["STEM", "Creativity", "Life Skills"],
                "parent_approved_only": False,
                "content_types": ["animated_video", "interactive_game"]
            }
        )
        self.assertEqual(ctrl_res.status_code, 200)
        self.assertIn("Life Skills", ctrl_res.json()["controls"]["allowed_categories"])

        # Update screen time and curfew
        st_res = client.put(
            f"/api/v1/parents/children/{child_id}/screen-time",
            headers=self.parent_headers,
            json={
                "daily_limit_minutes": 50,
                "curfew_start_time": "20:30",
                "curfew_end_time": "07:00",
                "curfew_enabled": True
            }
        )
        self.assertEqual(st_res.status_code, 200)
        self.assertEqual(st_res.json()["screen_time"]["daily_limit_minutes"], 50)

    def test_03_kids_mode_adventure_and_balance_engine(self):
        child_id = "c-aarav-07"
        adv_res = client.get(f"/api/v1/kids/{child_id}/adventure")
        self.assertEqual(adv_res.status_code, 200)
        adv_data = adv_res.json()

        self.assertIn("steps", adv_data)
        self.assertGreaterEqual(len(adv_data["steps"]), 1)
        self.assertIn("mascot_name", adv_data)
        self.assertIn("theme_title", adv_data)

        # Check if Money Adventure or Interactive choice game step is present
        choice_steps = [s for s in adv_data["steps"] if "Choice Game" in s.get("title", "") or "interactive" in s.get("step_type", "")]
        self.assertTrue(len(choice_steps) > 0)
        self.assertIn("content_item_id", choice_steps[0])

    def test_04_kids_feed_and_why_am_i_seeing_this_explainability(self):
        child_id = "c-aarav-07"
        feed_res = client.get(f"/api/v1/kids/{child_id}/feed?limit=6")
        self.assertEqual(feed_res.status_code, 200)
        feed_data = feed_res.json()
        self.assertIn("items", feed_data)
        self.assertGreater(len(feed_data["items"]), 0)

        # Check "Why am I seeing this?" transparent explainability
        content_id = feed_data["items"][0]["id"]
        exp_res = client.get(f"/api/v1/kids/{child_id}/feed/explain/{content_id}")
        self.assertEqual(exp_res.status_code, 200)
        exp_data = exp_res.json()

        self.assertIn("reasons", exp_data)
        self.assertIn("learning_balance_note", exp_data)
        self.assertTrue(exp_data["parent_allowed"])

    def test_05_kids_activity_and_quiz_submission(self):
        child_id = "c-aarav-07"
        # 1. Log activity with seeded content
        act_res = client.post(
            f"/api/v1/kids/{child_id}/activity",
            json={
                "content_item_id": "k-content-01",
                "activity_type": "interactive_choice",
                "dwell_time_seconds": 180,
                "child_reaction": "loved"
            }
        )
        self.assertIn(act_res.status_code, [200, 201])
        act_data = act_res.json()
        self.assertEqual(act_data["child_reaction"], "loved")
        self.assertGreater(act_data["stars_earned"], 0)

        # 2. Submit quiz response
        quiz_res = client.post(
            f"/api/v1/kids/{child_id}/quiz/submit",
            json={
                "quiz_id": "k-quiz-plant-01",
                "selected_option": "Sunlight"
            }
        )
        self.assertEqual(quiz_res.status_code, 200)
        qdata = quiz_res.json()
        self.assertTrue(qdata["is_correct"])
        self.assertIn("positive_feedback", qdata)
        self.assertGreater(qdata["stars_awarded"], 0)

        # 3. Check achievements
        ach_res = client.get(f"/api/v1/kids/{child_id}/achievements")
        self.assertEqual(ach_res.status_code, 200)
        ach_data = ach_res.json()
        self.assertIn("achievements", ach_data)
        self.assertGreaterEqual(len(ach_data["achievements"]), 1)

    def test_06_parent_dashboard_for_child(self):
        child_id = "c-aarav-07"
        dash_res = client.get(f"/api/v1/parents/children/{child_id}/dashboard", headers=self.parent_headers)
        self.assertEqual(dash_res.status_code, 200)
        d = dash_res.json()

        self.assertEqual(d["child_id"], child_id)
        self.assertIn("today_learning_minutes", d)
        self.assertIn("category_time_breakdown", d)
        self.assertIn("observed_interests", d)
        self.assertIn("parent_alerts", d)

    def test_07_kids_safe_search(self):
        child_id = "c-aarav-07"
        search_res = client.get(f"/api/v1/kids/{child_id}/safe-search?q=planet")
        self.assertEqual(search_res.status_code, 200)
        sdata = search_res.json()
        self.assertIn("items", sdata)
        self.assertIn("query", sdata)
        self.assertGreaterEqual(sdata["results_count"], 1)


if __name__ == "__main__":
    unittest.main()
