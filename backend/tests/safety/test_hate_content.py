import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app.safety.engine import SafetyEngine

class TestHateContentSafety(unittest.TestCase):
    """Verifies that hate speech, harassment, and discriminatory content is blocked."""

    def test_hate_speech_and_harassment_blocked(self):
        cases = [
            "We should kill all members of this group with hate speech",
            "racial slurs and cyberbullying guide against students",
            "doxxing and target harassment tutorial"
        ]
        for query in cases:
            res = SafetyEngine.audit_content(title=query, target_age=16)
            self.assertFalse(res["is_safe"], f"Failed to block hate query: {query}")
            self.assertEqual(res["verdict"], "BLOCK")

if __name__ == "__main__":
    unittest.main()
