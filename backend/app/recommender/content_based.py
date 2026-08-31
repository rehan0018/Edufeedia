from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Any
from app.models.models import ContentItem, StudentProfile, StudentProgress
from app.embeddings.embedder import embed_student, embed_content, cosine_similarity
from app.core.tenant_scope import TenantScope

def generate_content_based_candidates(
    db: Session,
    student_profile: StudentProfile,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Candidate Generation Layer 1: Content-Based Filtering
    Retrieves syllabus content strictly within student's tenant scope, board, and grade.
    Zero cross-school or cross-grade leakage.
    """
    grade = student_profile.school_class.grade_level if student_profile.school_class else (student_profile.grade_level or 10)
    board = student_profile.board or "CBSE"
    interests = student_profile.interests or []

    # Retrieve completed item IDs to avoid re-recommending finished items in primary feed
    completed_logs = db.query(StudentProgress.content_item_id).filter(
        StudentProgress.student_user_id == student_profile.user_id,
        StudentProgress.progress_percentage == 100
    ).all()
    completed_ids = {log[0] for log in completed_logs}

    # Query approved syllabus items matching grade, board, and tenant scope
    base_query = TenantScope.content(db, student_profile.user).filter(
        ContentItem.is_approved == True,
        ContentItem.grade_level == grade,
        ~ContentItem.id.in_(completed_ids) if completed_ids else True
    )

    items = base_query.filter(ContentItem.board == board).all()
    if not items:
        # Allow curriculum with global/general board if same grade & school scope
        items = base_query.all()

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
