import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from app.ai.llm_client import llm_client

class TestFailClosedSafety(unittest.TestCase):
    """Verifies that when safety engines or LLM providers fail/error, the system fails closed."""

    def test_safety_audit_exception_fails_closed(self):
        """If safety classification raises an unhandled error, output MUST NOT be passed to student."""
        with patch.object(llm_client, "_audit_output_safety", side_effect=RuntimeError("Safety engine offline")):
            response = llm_client.generate_socratic_response(
                question="Explain cellular respiration",
                curriculum_context="Mitochondria produce ATP",
                topic="Respiration",
                student_grade=10,
                subject="Biology"
            )
            # Must fail closed: response marked unsafe and replaced with fail-closed safety advisory
            self.assertFalse(response.get("is_safe", True))
            self.assertEqual(response.get("provider"), "safety_gate_fail_closed")

if __name__ == "__main__":
    unittest.main()
