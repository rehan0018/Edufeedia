from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime

from app.database import get_db
from app.models.models import User, ContentItem, StudentProgress, StudentProfile, SpacedRepetitionSchedule
from app.schemas.schemas import ContentItemOut, ProgressUpdate, ProgressResponse
from app.core.security import get_current_user, RoleChecker
from app.embeddings.embedder import embed_query, embed_content, cosine_similarity

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/explore")
def explore_content(
    query: str = None,
    subject: str = None,
    grade_level: int = None,
    board: str = None,
    content_type: str = None,
    difficulty: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    q = db.query(ContentItem).filter(ContentItem.is_approved == True)

    if query:
        search = f"%{query}%"
        q = q.filter(
            (ContentItem.title.ilike(search)) |
            (ContentItem.description.ilike(search)) |
            (ContentItem.topic.ilike(search)) |
            (ContentItem.subject.ilike(search))
        )
    if subject:
        q = q.filter(ContentItem.subject.ilike(f"%{subject}%"))
    if grade_level:
        q = q.filter(ContentItem.grade_level == grade_level)
    if board:
        q = q.filter(ContentItem.board == board)
    if content_type:
        q = q.filter(ContentItem.type == content_type)
    if difficulty:
        q = q.filter(ContentItem.difficulty == difficulty)

    items = q.order_by(ContentItem.created_at.desc()).offset(max(0, offset)).limit(min(100, max(1, limit))).all()

    # Get student progress if student
    completed_ids = set()
    if current_user.role == "student":
        completed_logs = db.query(StudentProgress.content_item_id).filter(
            StudentProgress.student_user_id == current_user.id,
            StudentProgress.progress_percentage == 100
        ).all()
        completed_ids = {log[0] for log in completed_logs}

    results = []
    for item in items:
        results.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "source_url": item.source_url,
            "source_platform": item.source_platform,
            "embed_code": item.embed_code,
            "type": item.type,
            "board": item.board,
            "grade_level": item.grade_level,
            "subject": item.subject,
            "topic": item.topic,
            "difficulty": item.difficulty,
            "duration_minutes": item.duration_minutes,
            "safety_score": item.safety_score,
            "edu_score": item.edu_score,
            "is_completed": item.id in completed_ids
        })

    return results

@router.get("/search")
def semantic_search_catalog(
    q: str,
    limit: int = 10,
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Performs 384-dimensional dense vector embedding semantic search over the approved educational catalog.
    Matches semantic intent, concepts, and synonyms rather than simple substring matching.
    """
    if not q or not q.strip():
        return {"query": q, "total_results": 0, "results": []}

    query_vec = embed_query(q.strip())
    approved_items = db.query(ContentItem).filter(ContentItem.is_approved == True).all()

    scored_items = []
    for item in approved_items:
        item_vec = item.embedding
        if not item_vec or len(item_vec) != len(query_vec):
            item_vec = embed_content(item.title, item.description or "", item.subject, item.topic, item.tags)

        sim = cosine_similarity(query_vec, item_vec)
        # Combine semantic cosine similarity with keyword booster
        kw_boost = 0.35 if (q.lower() in item.title.lower() or q.lower() in item.topic.lower() or q.lower() in item.subject.lower()) else 0.0
        final_score = min(1.0, sim + kw_boost)

        if final_score > 0.20: # Semantic relevance threshold
            scored_items.append({
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "subject": item.subject,
                "topic": item.topic,
                "grade_level": item.grade_level,
                "board": item.board,
                "type": item.type,
                "source_url": item.source_url,
                "source_platform": item.source_platform,
                "embed_code": item.embed_code,
                "duration_minutes": item.duration_minutes,
                "safety_score": item.safety_score,
                "edu_score": item.edu_score,
                "semantic_similarity": round(sim, 3),
                "relevance_score": round(final_score, 3),
                "relevance_percentage": int(round(final_score * 100))
            })

    scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
    results = scored_items[:limit]

    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }

@router.get("/{content_id}", response_model=ContentItemOut)
def get_content_item(
    content_id: str,
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    return item

@router.post("/progress", response_model=ProgressResponse)
def update_progress(
    progress_data: ProgressUpdate,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    item = db.query(ContentItem).filter(ContentItem.id == progress_data.content_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
        
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == current_user.id,
        StudentProgress.content_item_id == progress_data.content_item_id
    ).first()
    
    xp_earned = 0
    newly_completed = False
    
    if not progress:
        progress = StudentProgress(
            student_user_id=current_user.id,
            content_item_id=progress_data.content_item_id,
            progress_percentage=progress_data.progress_percentage
        )
        if progress_data.progress_percentage == 100:
            progress.completed_at = datetime.datetime.utcnow()
            newly_completed = True
        db.add(progress)
    else:
        was_completed = (progress.progress_percentage == 100)
        progress.progress_percentage = max(progress.progress_percentage, progress_data.progress_percentage)
        
        if progress.progress_percentage == 100 and not was_completed:
            progress.completed_at = datetime.datetime.utcnow()
            newly_completed = True
            
    if newly_completed:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if profile:
            profile.xp_score += 15
            xp_earned = 15
            
        existing_schedule = db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == current_user.id,
            SpacedRepetitionSchedule.subject == item.subject,
            SpacedRepetitionSchedule.topic == item.topic
        ).first()
        
        if not existing_schedule:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            schedule = SpacedRepetitionSchedule(
                student_user_id=current_user.id,
                subject=item.subject,
                topic=item.topic,
                interval_days=1,
                repetition_number=0,
                easiness_factor=2.50,
                next_review_date=tomorrow
            )
            db.add(schedule)
            
    db.commit()
    
    return {
        "status": "success",
        "completed": progress.progress_percentage == 100,
        "xp_earned": xp_earned
    }
