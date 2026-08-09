from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Any
from app.models.models import ContentItem, StudentProfile, StudentProgress
from app.embeddings.embedder import embed_student, embed_content, cosine_similarity

def generate_content_based_candidates(
    db: Session,
    student_profile: StudentProfile,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Candidate Generation Layer 1: Content-Based Filtering
    Retrieves syllabus content aligned with student's board, grade, and semantic interest vector.
    """
    grade = student_profile.school_class.grade_level if student_profile.school_class else 10
    board = student_profile.board or "CBSE"
    interests = student_profile.interests or ["Mathematics", "Science", "Coding"]

    # Retrieve completed item IDs to avoid re-recommending finished items in primary feed
    completed_logs = db.query(StudentProgress.content_item_id).filter(
        StudentProgress.student_user_id == student_profile.user_id,
        StudentProgress.progress_percentage == 100
    ).all()
    completed_ids = {log[0] for log in completed_logs}

    # Query approved syllabus items matching grade and board
    items = db.query(ContentItem).filter(
        ContentItem.is_approved == True,
        ContentItem.grade_level == grade,
        ContentItem.board == board,
        ~ContentItem.id.in_(completed_ids) if completed_ids else True
    ).all()

    # Fallback 1: match grade across any board if count is low
    if len(items) < 3:
        existing_ids = {i.id for i in items}
        more_grade_items = db.query(ContentItem).filter(
            ContentItem.is_approved == True,
            ContentItem.grade_level == grade,
            ~ContentItem.id.in_(completed_ids | existing_ids) if (completed_ids or existing_ids) else True
        ).all()
        items.extend(more_grade_items)

    # Fallback 2: general approved educational items across all grades/boards
    if len(items) < 3:
        existing_ids = {i.id for i in items}
        general_items = db.query(ContentItem).filter(
            ContentItem.is_approved == True,
            ~ContentItem.id.in_(completed_ids | existing_ids) if (completed_ids or existing_ids) else True
        ).all()
        items.extend(general_items)

    # Generate student profile semantic embedding vector
    student_vec = embed_student(
        interests=interests,
        board=board,
        grade_level=grade
    )

    candidates = []
    for item in items:
        # Compute or retrieve item embedding
        item_vec = item.embedding
        if not item_vec:
            item_vec = embed_content(
                title=item.title,
                description=item.description,
                subject=item.subject,
                topic=item.topic,
                tags=item.tags
            )

        # 1. Semantic content similarity (Sentence-BERT style cosine similarity)
        sim = cosine_similarity(student_vec, item_vec)

        # 2. Explicit interest keyword match
        interest_match = 1.0 if any(i.lower() in item.subject.lower() or i.lower() in item.topic.lower() for i in interests) else 0.4

        # 3. Grade & Board exact match
        grade_match = 1.0 if (item.grade_level == grade and item.board == board) else 0.7

        candidates.append({
            "content_item": item,
            "content_similarity": sim,
            "interest_match": interest_match,
            "grade_match": grade_match,
            "source": "content_based"
        })

    # Sort by semantic similarity
    candidates.sort(key=lambda x: x["content_similarity"], reverse=True)
    return candidates[:limit]
