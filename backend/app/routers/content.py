from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime

from app.database import get_db
from app.models.models import User, ContentItem, StudentProgress, StudentProfile, SpacedRepetitionSchedule
from app.schemas.schemas import ContentItemOut, ProgressUpdate, ProgressResponse
from app.core.security import get_current_user, RoleChecker

router = APIRouter(prefix="/content", tags=["content"])

@router.get("/{content_id}", response_model=ContentItemOut)
def get_content_item(
    content_id: str,
    current_user: User = Depends(RoleChecker(["student"])),
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
        
    # Check if progress record already exists
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
        # Check if it was completed previously
        was_completed = (progress.progress_percentage == 100)
        progress.progress_percentage = max(progress.progress_percentage, progress_data.progress_percentage)
        
        if progress.progress_percentage == 100 and not was_completed:
            progress.completed_at = datetime.datetime.utcnow()
            newly_completed = True
            
    if newly_completed:
        # 1. Add XP to student profile
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if profile:
            profile.xp_score += 15 # Earn 15 XP on completing a lesson
            xp_earned = 15
            
        # 2. Add item to Spaced Repetition Schedule if not already scheduled
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
