from typing import Dict, Any, List
from app.models.models import ContentItem, StudentProfile
from app.embeddings.embedder import cosine_similarity, embed_student, embed_content

# Hybrid feature weight coefficients
WEIGHT_CONTENT_SIMILARITY = 0.30
WEIGHT_STUDENT_INTEREST   = 0.20
WEIGHT_GRADE_BOARD_MATCH  = 0.15
WEIGHT_BEHAVIORAL_SCORE   = 0.15
WEIGHT_LEARNING_VALUE     = 0.10
WEIGHT_CONTENT_QUALITY    = 0.10

def compute_hybrid_rank_score(
    item: ContentItem,
    student_profile: StudentProfile,
    student_vector: List[float],
    behavioral_profile: Dict[str, float],
    candidate_source: str = "content_based"
) -> Dict[str, Any]:
    """
    Computes final relevance ranking score for a candidate item:
    Score = 0.30 * ContentSim + 0.20 * InterestMatch + 0.15 * GradeMatch + 0.15 * Behavioral + 0.10 * EduValue + 0.10 * Quality
    """
    grade = student_profile.school_class.grade_level if student_profile.school_class else 10
    board = student_profile.board or "CBSE"
    interests = student_profile.interests or []

    # 1. Content Semantic Similarity (0.0 to 1.0)
    item_vec = item.embedding
    if not item_vec:
        item_vec = embed_content(item.title, item.description, item.subject, item.topic, item.tags)
    content_sim = cosine_similarity(student_vector, item_vec)

    # 2. Student Interest Match (0.0 to 1.0)
    if not interests:
        # Neutral cold-start score
        interest_score = 0.5
    else:
        item_subj_topic = f"{item.subject} {item.topic}".lower()
        interest_hits = sum(1 for i in interests if i.lower() in item_subj_topic)
        interest_score = min(1.0, 0.4 + (interest_hits * 0.3)) if interest_hits > 0 else 0.3

    # 3. Grade & Board Fit (0.0 to 1.0)
    grade_score = 1.0 if (item.grade_level == grade and item.board == board) else (0.8 if item.grade_level == grade else 0.5)

    # 4. Behavioral / Implicit Feedback Score (0.0 to 1.0)
    user_subj_affinity = behavioral_profile.get(item.subject, 0.5)
    behavioral_score = max(0.0, min(1.0, 0.5 + (user_subj_affinity * 0.5)))

    # 5. Learning & Educational Value (0.0 to 1.0)
    edu_score = float(item.edu_score or 90) / 100.0

    # 6. Content Quality & Safety (0.0 to 1.0)
    safety_norm = float(item.safety_score or 100) / 100.0
    quality_score = safety_norm

    # Calculate final hybrid weighted sum
    total_score = (
        (WEIGHT_CONTENT_SIMILARITY * content_sim) +
        (WEIGHT_STUDENT_INTEREST * interest_score) +
        (WEIGHT_GRADE_BOARD_MATCH * grade_score) +
        (WEIGHT_BEHAVIORAL_SCORE * behavioral_score) +
        (WEIGHT_LEARNING_VALUE * edu_score) +
        (WEIGHT_CONTENT_QUALITY * quality_score)
    )

    relevance_pct = int(round(total_score * 100))

    return {
        "content_similarity": round(content_sim, 3),
        "interest_match": round(interest_score, 3),
        "grade_match": round(grade_score, 3),
        "behavioral_score": round(behavioral_score, 3),
        "learning_value": round(edu_score, 3),
        "content_quality": round(quality_score, 3),
        "total_relevance_score": round(total_score, 4),
        "relevance_percentage": relevance_pct,
        "candidate_source": candidate_source
    }
