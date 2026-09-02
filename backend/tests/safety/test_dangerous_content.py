import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app.safety.engine import SafetyEngine

class TestDangerousContentSafety(unittest.TestCase):
    """Verifies that violent, weapons, explosives, and self-harm content is blocked."""

    def test_dangerous_activities_and_weapons_blocked(self):
        cases = [
            "how to make an explosive and homemade bomb",
            "gun making and pipe bomb tutorial",
            "how to commit suicide methods",
            "synthesize methamphetamine and cook meth"
        ]
        for query in cases:
            res = SafetyEngine.audit_content(title=query, target_age=15)
            self.assertFalse(res["is_safe"], f"Failed to block dangerous query: {query}")
            self.assertEqual(res["verdict"], "BLOCK")

if __name__ == "__main__":
    unittest.main()
