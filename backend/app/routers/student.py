from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import datetime

from app.database import get_db
from app.models.models import User, StudentProfile, StudentProgress, QuizAttempt
from app.schemas.schemas import StudentProfileOut, StudentProfileUpdate, ContentItemOut
from app.core.security import get_current_user, RoleChecker
from app.core.algorithms import generate_daily_feed

router = APIRouter(prefix="/students", tags=["students"])

@router.get("/profile", response_model=StudentProfileOut)
def get_profile(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile

@router.put("/profile", response_model=StudentProfileOut)
def update_profile(
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    if profile_data.board is not None:
        profile.board = profile_data.board
    if profile_data.interests is not None:
        profile.interests = profile_data.interests
    if profile_data.learning_preference is not None:
        profile.learning_preference = profile_data.learning_preference
        
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/feed", response_model=Dict[str, Any])
def get_daily_learning_feed(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    # Check streak logic: if logged in on consecutive days, increment streak.
    today = datetime.date.today()
    if profile.last_active_date:
        delta = today - profile.last_active_date
        if delta.days == 1:
            profile.streak_count += 1
        elif delta.days > 1:
            profile.streak_count = 1  # Reset streak if missed a day
    else:
        profile.streak_count = 1
        
    profile.last_active_date = today
    db.commit()
    
    feed_items = generate_daily_feed(db, current_user.id)
    
    # Check if they have a quiz for today's items
    # In this MVP, we create a unified daily quiz from feed item quizzes
    quiz_id = None
    if feed_items:
        # Find first approved quiz associated with items in the feed
        from app.models.models import Quiz
        item_ids = [item.id for item in feed_items]
        quiz = db.query(Quiz).filter(Quiz.content_item_id.in_(item_ids)).first()
        if quiz:
            quiz_id = quiz.id
            
    # Serialize feed items
    serialized_feed = []
    for item in feed_items:
        serialized_feed.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "source_url": item.source_url,
            "source_platform": item.source_platform,
            "embed_code": item.embed_code,
            "type": item.type,
            "subject": item.subject,
            "topic": item.topic,
            "duration_minutes": item.duration_minutes,
            "difficulty": item.difficulty
        })

    return {
        "greeting": f"Good morning, {current_user.first_name}! 👋",
        "streak": profile.streak_count,
        "xp": profile.xp_score,
        "learning_plan": serialized_feed,
        "daily_quiz": {
            "quiz_id": quiz_id,
            "number_of_questions": 5 if quiz_id else 0
        } if quiz_id else None
    }

@router.get("/dashboard", response_model=Dict[str, Any])
def get_student_dashboard(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
    # Get subjects progress
    completed_logs = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == current_user.id,
        StudentProgress.progress_percentage == 100
    ).all()
    
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == current_user.id
    ).all()
    
    # Calculate average quiz accuracy
    total_attempts = len(attempts)
    avg_accuracy = 0.0
    if total_attempts > 0:
        avg_accuracy = float(sum(a.accuracy_percentage for a in attempts) / total_attempts)
        
    # Categorize completed videos count by subject
    subject_mastery = {}
    for log in completed_logs:
        sub = log.content_item.subject
        subject_mastery[sub] = subject_mastery.get(sub, 0) + 1
        
    # Calculate streak progress
    return {
        "xp": profile.xp_score,
        "streak": profile.streak_count,
        "total_lessons_completed": len(completed_logs),
        "average_quiz_accuracy": avg_accuracy,
        "subject_mastery": [
            {"subject": sub, "completed_lessons": count} for sub, count in subject_mastery.items()
        ]
    }
