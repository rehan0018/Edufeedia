from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.models import User, ContentItem, StudentProgress, StudentProfile, SpacedRepetitionSchedule, ContentReport
from app.schemas.schemas import ContentItemOut, ProgressUpdate, ProgressResponse, ContentReportCreate, ContentReportOut
from app.core.security import get_current_user, RoleChecker
from app.core.access_policy import require_learning_access, require_authenticated_user
from app.core.age_policy import StudentAgePolicy
from app.safety.engine import SafetyEngine
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
    current_user: User = Depends(require_learning_access),
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

    # Get student progress and apply age safety filtering if student
    completed_ids = set()
    target_age = 15
    if current_user.role == "student":
        target_age = StudentAgePolicy.get_student_age(current_user.student_profile)
        completed_logs = db.query(StudentProgress.content_item_id).filter(
            StudentProgress.student_user_id == current_user.id,
            StudentProgress.progress_percentage == 100
        ).all()
        completed_ids = {log[0] for log in completed_logs}

    results = []
    for item in items:
        if current_user.role == "student":
            is_safe = SafetyEngine.is_safe_for_students(
                title=item.title,
                description=item.description or "",
                tags=item.tags,
                target_age=target_age
            )
            if not is_safe or (item.safety_score is not None and item.safety_score < 80):
                continue

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
    current_user: User = Depends(require_learning_access),
    db: Session = Depends(get_db)
):
    """
    Performs 384-dimensional dense vector embedding semantic search over the approved educational catalog.
    Matches semantic intent, concepts, and synonyms rather than simple substring matching.
    """
    if not q or not q.strip():
        return {"query": q, "total_results": 0, "results": []}

    target_age = 15
    if current_user.role == "student":
        target_age = StudentAgePolicy.get_student_age(current_user.student_profile)

    query_vec = embed_query(q.strip())
    approved_items = db.query(ContentItem).filter(ContentItem.is_approved == True).all()

    scored_items = []
    for item in approved_items:
        if current_user.role == "student":
            is_safe = SafetyEngine.is_safe_for_students(
                title=item.title,
                description=item.description or "",
                tags=item.tags,
                target_age=target_age
            )
            if not is_safe or (item.safety_score is not None and item.safety_score < 80):
                continue

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
    current_user: User = Depends(require_learning_access),
    db: Session = Depends(get_db)
):
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    if current_user.role == "student" and not item.is_approved:
        raise HTTPException(status_code=404, detail="Content item not found or pending administrative approval")
    return item

@router.post("/progress", response_model=ProgressResponse)
def update_progress(
    progress_data: ProgressUpdate,
    current_user: User = Depends(require_learning_access),
    db: Session = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can track personal progress")
    item = db.query(ContentItem).filter(
        ContentItem.id == progress_data.content_item_id,
        ContentItem.is_approved == True
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found or not approved for students")
        
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
            progress.completed_at = datetime.datetime.now(datetime.timezone.utc)
            newly_completed = True
        db.add(progress)
    else:
        was_completed = (progress.progress_percentage == 100)
        progress.progress_percentage = max(progress.progress_percentage, progress_data.progress_percentage)
        
        if progress.progress_percentage == 100 and not was_completed:
            progress.completed_at = datetime.datetime.now(datetime.timezone.utc)
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
    try:
        db.commit()
    except Exception:
        db.rollback()
        existing = db.query(StudentProgress).filter(
            StudentProgress.student_user_id == current_user.id,
            StudentProgress.content_item_id == progress_data.content_item_id
        ).first()
        if existing:
            existing.progress_percentage = max(existing.progress_percentage, progress_data.progress_percentage)
            if existing.progress_percentage == 100 and not existing.completed_at:
                existing.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            progress = existing
    
    return {
        "status": "success",
        "completed": progress.progress_percentage == 100,
        "xp_earned": xp_earned
    }

@router.post("/report", response_model=ContentReportOut)
def report_content(
    report_data: ContentReportCreate,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Submits a content report from student or parent into the moderation queue.
    Closes the feedback loop for unsafe, inaccurate, or developmentally inappropriate material.
    """
    content_item = db.query(ContentItem).filter(ContentItem.id == report_data.content_item_id).first()
    if not content_item:
        raise HTTPException(status_code=404, detail="Content item not found")

    report = ContentReport(
        reporter_user_id=current_user.id,
        content_item_id=report_data.content_item_id,
        reason=report_data.reason,
        details=report_data.details,
        status="pending_review"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ContentReportOut(
        id=report.id,
        content_item_id=report.content_item_id,
        content_title=content_item.title,
        reporter_id=report.reporter_user_id,
        reason=report.reason,
        details=report.details,
        status=report.status,
        created_at=report.created_at
    )

@router.post("/{content_id}/report", response_model=ContentReportOut)
def report_content_by_id(
    content_id: str,
    reason: str = "Other",
    details: Optional[str] = None,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Direct resource endpoint for reporting a specific content item by path parameter.
    """
    report_data = ContentReportCreate(
        content_item_id=content_id,
        reason=reason if reason in ["Unsafe", "Incorrect", "Not age appropriate", "Not educational", "Broken", "Other"] else "Other",
        details=details
    )
    return report_content(report_data=report_data, current_user=current_user, db=db)
