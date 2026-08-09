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

    # Sync live database to owner's read-only Excel workbook
    try:
        from app.core.excel_exporter import sync_database_to_excel
        sync_database_to_excel(db)
    except Exception as e:
        print(f"[Excel Sync Warning]: {e}")

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
    
    from app.recommender.hybrid import recommender_instance
    rec_result = recommender_instance.get_personalized_recommendations(db, current_user.id, limit=4)
    feed_items = rec_result.get("items", [])
    
    # Check if they have a quiz for today's items
    quiz_id = None
    if feed_items:
        from app.models.models import Quiz
        item_ids = [item["id"] for item in feed_items]
        quiz = db.query(Quiz).filter(Quiz.content_item_id.in_(item_ids)).first()
        if quiz:
            quiz_id = quiz.id

    return {
        "greeting": f"Good morning, {current_user.first_name}! 👋",
        "streak": profile.streak_count,
        "xp": profile.xp_score,
        "total_candidates_evaluated": rec_result.get("total_candidates_evaluated", len(feed_items)),
        "learning_plan": feed_items,
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

@router.get("/leaderboard")
def get_leaderboard(
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent"])),
    db: Session = Depends(get_db)
):
    profiles = db.query(StudentProfile).order_by(StudentProfile.xp_score.desc()).all()
    
    leaderboard = []
    for rank, p in enumerate(profiles, start=1):
        u = p.user
        if not u:
            continue
        
        # Determine level from XP
        xp = p.xp_score
        if xp >= 1000:
            level = 5
        elif xp >= 600:
            level = 4
        elif xp >= 300:
            level = 3
        elif xp >= 100:
            level = 2
        else:
            level = 1

        leaderboard.append({
            "rank": rank,
            "user_id": u.id,
            "name": f"{u.first_name} {u.last_name[0] if u.last_name else ''}.",
            "xp": p.xp_score,
            "streak": p.streak_count,
            "level": level,
            "is_current_user": (u.id == current_user.id)
        })

    return leaderboard

@router.get("/badges")
def get_student_badges(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    from app.models.models import Badge, UserBadge
    
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    xp = profile.xp_score
    if xp >= 1000:
        level = 5
        next_xp = 1500
        level_title = "Grandmaster Scholar"
    elif xp >= 600:
        level = 4
        next_xp = 1000
        level_title = "Master Mind"
    elif xp >= 300:
        level = 3
        next_xp = 600
        level_title = "Active Scholar"
    elif xp >= 100:
        level = 2
        next_xp = 300
        level_title = "Rising Scholar"
    else:
        level = 1
        next_xp = 100
        level_title = "Novice Scholar"

    # Query all system badges
    all_badges = db.query(Badge).all()
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == current_user.id).all()
    unlocked_badge_ids = {ub.badge_id: ub.unlocked_at for ub in user_badges}

    # Evaluate dynamic unlocks if not already persisted
    completed_count = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == current_user.id,
        StudentProgress.progress_percentage == 100
    ).count()

    has_perfect_quiz = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == current_user.id,
        QuizAttempt.accuracy_percentage >= 100.0
    ).first() is not None

    badges_out = []
    unlocked_count = 0

    for b in all_badges:
        is_unlocked = b.id in unlocked_badge_ids
        unlocked_at = unlocked_badge_ids.get(b.id)

        # Dynamic check
        if not is_unlocked:
            should_unlock = False
            if b.code == "streak_7" and profile.streak_count >= 7:
                should_unlock = True
            elif b.code == "streak_3" and profile.streak_count >= 3:
                should_unlock = True
            elif b.code == "quiz_100" and has_perfect_quiz:
                should_unlock = True
            elif b.code == "lesson_5" and completed_count >= 5:
                should_unlock = True
            elif b.code == "scholar_xp" and profile.xp_score >= 300:
                should_unlock = True

            if should_unlock:
                new_ub = UserBadge(user_id=current_user.id, badge_id=b.id)
                db.add(new_ub)
                db.commit()
                is_unlocked = True
                unlocked_at = new_ub.unlocked_at

        if is_unlocked:
            unlocked_count += 1

        badges_out.append({
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "category": b.category,
            "xp_bonus": b.xp_bonus,
            "unlocked": is_unlocked,
            "unlocked_at": unlocked_at.isoformat() if unlocked_at else None
        })

    return {
        "total_badges": len(all_badges),
        "unlocked_count": unlocked_count,
        "level": level,
        "current_xp": xp,
        "next_level_xp": next_xp,
        "level_title": level_title,
        "badges": badges_out
    }

from app.learning.analytics import compute_student_topic_mastery
from app.schemas.schemas import TopicMasteryResponse

@router.get("/analytics/mastery", response_model=TopicMasteryResponse)
def get_student_topic_mastery(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Computes topic-level mastery rates, identifies weak topics (<60%),
    and auto-activates priority SM-2 spaced repetition schedules.
    """
    mastery_report = compute_student_topic_mastery(db=db, student_id=current_user.id)
    return mastery_report
