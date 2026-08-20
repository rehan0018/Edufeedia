import unittest
from app.safety.engine import SafetyEngine

class TestAdultContentSafety(unittest.TestCase):
    """Verifies that all sexually explicit and adult material is strictly blocked."""

    def test_adult_keywords_blocked(self):
        cases = [
            "Watch adult 18+ explicit sex videos uncensored",
            "Nude photos and pornography streaming sites",
            "Erotic roleplay and explicit sex stories"
        ]
        for query in cases:
            res = SafetyEngine.audit_content(title=query, target_age=14)
            self.assertFalse(res["is_safe"], f"Failed to block adult query: {query}")
            self.assertEqual(res["verdict"], "BLOCK")

if __name__ == "__main__":
    unittest.main()
