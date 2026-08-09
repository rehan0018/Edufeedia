from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import datetime

from app.models.models import User, ContentItem, StudentProfile, StudentProgress, QuizAttempt, SpacedRepetitionSchedule
from app.embeddings.embedder import embed_student, embed_content, cosine_similarity

class RecommendationFeatureBuilder:
    """
    Feature Builder for Two-Stage Machine Learning Recommendation.
    Constructs dense tabular feature vectors for (student, content_item) interaction pairs.
    """

    @classmethod
    def extract_interaction_features(
        cls,
        db: Session,
        student_user: User,
        item: ContentItem,
        weak_topics: Optional[List[str]] = None,
        due_schedule_topics: Optional[List[str]] = None
    ) -> Dict[str, float]:
        profile = student_user.student_profile
        student_grade = profile.school_class.grade_level if (profile and profile.school_class) else 10
        student_board = profile.board if profile else "CBSE"
        interests = profile.interests if profile else []

        # 1. Grade & Board Alignment Features
        grade_delta = abs(student_grade - item.grade_level)
        grade_match_score = max(0.0, 1.0 - (grade_delta * 0.35))
        board_match = 1.0 if (item.board == student_board) else 0.50

        # 2. Pedagogical Weak-Topic Diagnostic Feature
        is_weak_topic = 1.0 if (weak_topics and item.topic in weak_topics) else 0.0

        # 3. Spaced Repetition Due Urgency Feature
        is_spaced_due = 1.0 if (due_schedule_topics and item.topic in due_schedule_topics) else 0.0

        # 4. Semantic Concept & Interest Cosine Similarity Feature
        student_vec = embed_student(interests, student_board, student_grade)
        item_vec = item.embedding
        if not item_vec or len(item_vec) != len(student_vec):
            item_vec = embed_content(item.title, item.description or "", item.subject, item.topic, item.tags)
        semantic_sim = cosine_similarity(student_vec, item_vec)

        # 5. Quality & Safety Normalized Features
        safety_norm = float(item.safety_score) / 100.0 if item.safety_score else 0.95
        edu_norm = float(item.edu_score) / 100.0 if item.edu_score else 0.85

        # 6. Difficulty Match Feature
        diff_score = 0.85
        if item.difficulty == "medium":
            diff_score = 1.0
        elif item.difficulty == "hard" and student_grade >= 11:
            diff_score = 0.95

        return {
            "grade_match_score": round(grade_match_score, 4),
            "board_match": round(board_match, 4),
            "is_weak_topic": is_weak_topic,
            "is_spaced_due": is_spaced_due,
            "semantic_sim": round(semantic_sim, 4),
            "safety_norm": round(safety_norm, 4),
            "edu_norm": round(edu_norm, 4),
            "diff_score": round(diff_score, 4)
        }
