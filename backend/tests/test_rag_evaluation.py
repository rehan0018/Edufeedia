import unittest
import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.evaluator import rag_evaluator, GOLDEN_EVALUATION_DATASET
from app.safety.policy_engine import policy_engine
from app.safety.content_classifier import content_classifier
from app.safety.age_policy import age_policy
from app.core.security import create_access_token, revoke_token, is_token_revoked
from app.core.redis_client import redis_client
import datetime

class TestRAGEvaluationAndSafety(unittest.TestCase):
    def setUp(self):
        redis_client.clear_all()

    def test_rag_retrieval_benchmark_metrics(self):
        """Verify RAG retrieval achieves high benchmark MRR, Precision, and Recall."""
        metrics = rag_evaluator.evaluate_retrieval(k=3)
        self.assertGreaterEqual(metrics["mrr@3"], 0.75, "RAG MRR@3 must be >= 0.75 on golden benchmark")
        self.assertGreaterEqual(metrics["recall@3"], 0.75, "RAG Recall@3 must be >= 0.75 on golden benchmark")

    def test_safety_gate_evaluation_metrics(self):
        """Verify content safety gate detects unsafe queries and prompt injections with 100% defense."""
        metrics = rag_evaluator.evaluate_safety_gate()
        self.assertEqual(metrics["safety_classification_accuracy"], 1.0)
        self.assertEqual(metrics["adversarial_defense_rate"], 1.0)

    def test_policy_engine_submission_eval(self):
        """Verify PolicyEngine approves high-value educational content and rejects harmful text."""
        # Benign educational content
        good_eval = policy_engine.evaluate_content_submission(
            title="Introduction to Photosynthesis and ATP Synthesis",
            text="In plant cells, chloroplasts utilize chlorophyll pigments to absorb photons and synthesize glucose and oxygen through light-dependent reactions.",
            grade_level=10
        )
        self.assertTrue(good_eval["is_approved"])
        self.assertEqual(good_eval["decision"], "APPROVE")

        # Inappropriate content
        bad_eval = policy_engine.evaluate_content_submission(
            title="Dangerous guide to weapons",
            text="Here is how to make explosives and weapons at home.",
            grade_level=10
        )
        self.assertFalse(bad_eval["is_approved"])
        self.assertEqual(bad_eval["decision"], "REJECT")

    def test_age_policy_consent_rules(self):
        """Verify AgePolicy enforces DPDP/COPPA guardian consent thresholds."""
        # 13 year old requires guardian consent
        dob_minor = datetime.date(2013, 1, 1)
        res_minor = age_policy.validate_student_age(dob_minor)
        self.assertTrue(res_minor["is_eligible"])
        self.assertTrue(res_minor["requires_guardian_consent"])

        # 17 year old student
        dob_senior = datetime.date(2009, 1, 1)
        res_senior = age_policy.validate_student_age(dob_senior)
        self.assertTrue(res_senior["is_eligible"])

    def test_token_revocation_blacklist(self):
        """Verify JWT revocation in Redis terminates session immediately."""
        token = create_access_token(data={"sub": "student@apexschool.edu", "role": "student"})
        self.assertFalse(is_token_revoked(token))

        # Revoke token
        revoke_token(token, ttl_seconds=3600)
        self.assertTrue(is_token_revoked(token))

if __name__ == "__main__":
    unittest.main()
