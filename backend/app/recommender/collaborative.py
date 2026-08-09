from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.models import UserInteraction, ContentItem, StudentProfile, StudentProgress

def generate_collaborative_candidates(
    db: Session,
    student_profile: StudentProfile,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Candidate Generation Layer 2: Collaborative / Behavioral Filtering
    Finds content positively engaged with by students with similar learning behaviors in the same grade.
    """
    user_id = student_profile.user_id
    grade = student_profile.school_class.grade_level if student_profile.school_class else 10

    # Get items the current student has already completed
    completed_logs = db.query(StudentProgress.content_item_id).filter(
        StudentProgress.student_user_id == user_id,
        StudentProgress.progress_percentage == 100
    ).all()
    completed_ids = {log[0] for log in completed_logs}

    # Query interactions from other peers in the same class or grade
    peer_interactions = db.query(UserInteraction).join(ContentItem).filter(
        UserInteraction.user_id != user_id,
        ContentItem.grade_level == grade,
        ContentItem.is_approved == True,
        ~ContentItem.id.in_(completed_ids) if completed_ids else True,
        UserInteraction.weight > 0 # Only positive engagement
    ).all()

    # Aggregate item engagement scores across peers
    item_scores: Dict[str, float] = {}
    items_map: Dict[str, ContentItem] = {}

    for inter in peer_interactions:
        cid = inter.content_item_id
        item_scores[cid] = item_scores.get(cid, 0.0) + float(inter.weight)
        items_map[cid] = inter.content_item

    if not item_scores:
        return []

    max_score = max(item_scores.values()) or 1.0

    candidates = []
    for cid, raw_score in item_scores.items():
        norm_score = min(1.0, round(raw_score / max_score, 3))
        item = items_map[cid]
        candidates.append({
            "content_item": item,
            "collaborative_score": norm_score,
            "source": "collaborative"
        })

    candidates.sort(key=lambda x: x["collaborative_score"], reverse=True)
    return candidates[:limit]
