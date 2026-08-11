import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.models import User, ContentItem
from app.recommender.feature_builder import RecommendationFeatureBuilder
from app.recommender.ml_ranker import TwoStageMLRanker

class TestTwoStageRecommender(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.student = self.db.query(User).filter(User.email == "rahul@apexschool.edu").first()
        self.candidate_items = self.db.query(ContentItem).filter(ContentItem.is_approved == True).limit(5).all()

    def tearDown(self):
        self.db.close()

    def test_feature_extraction(self):
        self.assertIsNotNone(self.student)
        self.assertGreater(len(self.candidate_items), 0)

        item = self.candidate_items[0]
        features = RecommendationFeatureBuilder.extract_interaction_features(
            db=self.db,
            student_user=self.student,
            item=item,
            weak_topics=["Newton's Laws"],
            due_schedule_topics=["Quadratic Equations"]
        )

        self.assertIn("grade_match_score", features)
        self.assertIn("board_match", features)
        self.assertIn("is_weak_topic", features)
        self.assertIn("is_spaced_due", features)
        self.assertIn("semantic_sim", features)
        self.assertIn("safety_norm", features)
        self.assertIn("edu_norm", features)

    def test_two_stage_ml_ranking(self):
        ranked = TwoStageMLRanker.rank_candidates(
            db=self.db,
            student_user=self.student,
            candidate_items=self.candidate_items,
            top_n=3
        )

        self.assertEqual(len(ranked), min(3, len(self.candidate_items)))
        for r in ranked:
            self.assertIn("item", r)
            self.assertIn("score", r)
            self.assertIn("reason", r)
            self.assertGreaterEqual(r["score"], 0.0)
            self.assertLessEqual(r["score"], 1.0)

        # Verify items are in descending order of ranking score
        scores = [r["score"] for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_learning_loop_dynamic_reranking(self):
        """
        Validates the educational closed loop:
        When a topic is flagged as weak/due for revision, its score is boosted
        and it is prioritized with an explainable pedagogical badge.
        """
        item_normal = self.candidate_items[0]

        # Normal extraction
        f_normal = RecommendationFeatureBuilder.extract_interaction_features(
            db=self.db,
            student_user=self.student,
            item=item_normal,
            weak_topics=[],
            due_schedule_topics=[]
        )

        # Extraction when topic is flagged weak
        f_boosted = RecommendationFeatureBuilder.extract_interaction_features(
            db=self.db,
            student_user=self.student,
            item=item_normal,
            weak_topics=[item_normal.topic],
            due_schedule_topics=[item_normal.topic]
        )

        self.assertEqual(f_normal["is_weak_topic"], 0.0)
        self.assertEqual(f_normal["is_spaced_due"], 0.0)
        self.assertEqual(f_boosted["is_weak_topic"], 1.0)
        self.assertEqual(f_boosted["is_spaced_due"], 1.0)

        # Pointwise score under normal vs weak topic
        score_normal = TwoStageMLRanker.compute_pointwise_score(f_normal)
        score_boosted = TwoStageMLRanker.compute_pointwise_score(f_boosted)
        self.assertGreater(score_boosted, score_normal)

if __name__ == "__main__":
    unittest.main()
