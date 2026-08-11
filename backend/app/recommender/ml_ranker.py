import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import datetime

from app.models.models import User, ContentItem, StudentProgress, SpacedRepetitionSchedule
from app.recommender.feature_builder import RecommendationFeatureBuilder
from app.learning.analytics import StudentAnalyticsEngine

class TwoStageMLRanker:
    """
    Two-Stage Machine Learning Recommender:
    - Stage 1: Candidate Generation (Content, Collaborative, Spaced Queues)
    - Stage 2: Dense Feature Extraction & GBDT-style Pointwise Ranking Model
    """

    # Feature Importance Weights for Pointwise Gradient Scoring
    FEATURE_WEIGHTS = {
        "is_spaced_due": 0.30,       # Spaced review prioritized for long-term retention
        "is_weak_topic": 0.25,       # Diagnostic weak-topic intervention
        "grade_match_score": 0.20,   # Age and curriculum suitability
        "semantic_sim": 0.15,        # Conceptual interest match
        "edu_norm": 0.05,            # Pedagogical depth
        "board_match": 0.05          # Examination board syllabus
    }

    @classmethod
    def rank_candidates(
        cls,
        db: Session,
        student_user: User,
        candidate_items: List[ContentItem],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        if not candidate_items:
            return []

        # 1. Fetch Weak Topics & Due Schedules
        analytics = StudentAnalyticsEngine.get_student_mastery_report(db, student_user.id)
        weak_topics = [w["topic"] for w in analytics.get("weak_topics", [])]

        today = datetime.date.today()
        due_schedules = db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student_user.id,
            SpacedRepetitionSchedule.next_review_date <= today
        ).all()
        due_topics = [s.topic for s in due_schedules]

        # 2. Extract Features & Compute Pointwise Ranking Scores
        scored_candidates = []
        for item in candidate_items:
            features = RecommendationFeatureBuilder.extract_interaction_features(
                db=db,
                student_user=student_user,
                item=item,
                weak_topics=weak_topics,
                due_schedule_topics=due_topics
            )

            ranking_score = cls.compute_pointwise_score(features)

            # Explainable Recommendation Reason
            reason = "Recommended for your curriculum"
            if features["is_spaced_due"] > 0:
                reason = "Active Recall Review (Spaced Repetition)"
            elif features["is_weak_topic"] > 0:
                reason = f"Targeted Practice ({item.topic})"
            elif features["semantic_sim"] > 0.40:
                reason = "Matches your learning interests"

            scored_candidates.append({
                "item": item,
                "score": ranking_score,
                "features": features,
                "reason": reason
            })

        # 3. Sort by Final Ranking Score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        return scored_candidates[:top_n]

    @classmethod
    def compute_pointwise_score(cls, features: Dict[str, float]) -> float:
        """
        Computes calibrated sigmoidal pointwise ranking score from feature vector.
        """
        raw_logit = 0.0
        for feat_name, weight in cls.FEATURE_WEIGHTS.items():
            raw_logit += features.get(feat_name, 0.0) * weight

        # Non-linear boost: If spaced due AND weak topic, amplify score
        if features.get("is_spaced_due", 0) > 0 and features.get("is_weak_topic", 0) > 0:
            raw_logit += 0.20

        # Sigmoidal Calibration to [0.0, 1.0]
        ranking_score = 1.0 / (1.0 + math.exp(-3.0 * (raw_logit - 0.40)))
        return round(max(0.05, min(0.99, ranking_score)), 4)
