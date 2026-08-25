from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import datetime

from app.database import get_db
from app.models.models import User, StudentProfile, StudentProgress, QuizAttempt, SpacedRepetitionSchedule
from app.schemas.schemas import StudentProfileOut, StudentProfileUpdate, ContentItemOut, LearningHealthOut
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

from app.schemas.schemas import StudentOnboardingRequest

@router.post("/onboarding", response_model=StudentProfileOut)
def complete_student_onboarding(
    req: StudentOnboardingRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Onboarding Completion Endpoint:
    Allows newly registered or OAuth Google students to supply their verified date of birth,
    academic grade, school/board alignment, and real subject interests.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    # Validate student age
    today = datetime.date.today()
    dob = req.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 10 or age >= 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student age {age} not supported. Edufeedia is designed specifically for students aged 10 to 17."
        )

    profile.date_of_birth = req.date_of_birth
    profile.grade_level = req.grade_level or profile.grade_level or 10
    profile.board = req.board or profile.board or "CBSE"
    if req.interests:
        profile.interests = req.interests
    if req.learning_preference:
        profile.learning_preference = req.learning_preference

    profile.onboarding_status = "COMPLETED"

    db.commit()
    db.refresh(profile)
    return profile

@router.post("/activity", response_model=Dict[str, Any])
def record_student_activity(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Explicit Activity Tracking Endpoint:
    Registers a study session and advances the student's daily streak count idempotently.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    today = datetime.date.today()
    streak_advanced = False

    if profile.last_active_date:
        delta = today - profile.last_active_date
        if delta.days == 1:
            profile.streak_count += 1
            streak_advanced = True
        elif delta.days > 1:
            profile.streak_count = 1
            streak_advanced = True
    else:
        profile.streak_count = 1
        streak_advanced = True

    profile.last_active_date = today
    db.commit()
    db.refresh(profile)

    return {
        "status": "success",
        "streak_count": profile.streak_count,
        "last_active_date": str(profile.last_active_date),
        "streak_advanced": streak_advanced
    }

@router.get("/feed", response_model=Dict[str, Any])
def get_daily_learning_feed(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Read-Only Daily Learning Feed:
    Retrieves personalized curriculum recommendations without mutating user streak or profile state.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
        
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
        if log.content_item:
            subj = log.content_item.subject
            subject_mastery[subj] = subject_mastery.get(subj, 0) + 1
            
    # Recent activity
    recent_activity = []
    recent_logs = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == current_user.id
    ).order_by(StudentProgress.updated_at.desc()).limit(5).all()
    
    for r in recent_logs:
        if r.content_item:
            recent_activity.append({
                "title": r.content_item.title,
                "type": r.content_item.type,
                "progress": r.progress_percentage,
                "last_accessed": r.updated_at.isoformat() if r.updated_at else None
            })
            
    return {
        "xp": profile.xp_score,
        "streak": profile.streak_count,
        "total_lessons_completed": len(completed_logs),
        "average_quiz_accuracy": round(avg_accuracy, 1),
        "subject_mastery": subject_mastery,
        "recent_activity": recent_activity
    }

@router.get("/leaderboard", response_model=List[Dict[str, Any]])
def get_leaderboard(
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent"])),
    db: Session = Depends(get_db)
):
    """
    Privacy-preserving leaderboard:
    Displays student rank, masked anonymous identifiers, XP, and level within the user's school tenant.
    """
    if current_user.school_id:
        profiles = db.query(StudentProfile).join(User, StudentProfile.user_id == User.id).filter(
            User.school_id == current_user.school_id
        ).order_by(StudentProfile.xp_score.desc()).all()
    else:
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

        is_current = (u.id == current_user.id)
        # Protect peer UUIDs and PII from unauthorized scraping
        safe_user_id = u.id if is_current else f"learner_{rank:03d}"
        display_name = f"{u.first_name} {u.last_name[0] if u.last_name else ''}." if is_current else f"{u.first_name[0]}*** {u.last_name[0] if u.last_name else ''}."

        leaderboard.append({
            "rank": rank,
            "user_id": safe_user_id,
            "name": display_name,
            "xp": p.xp_score,
            "streak": p.streak_count,
            "level": level,
            "is_current_user": is_current
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
    new_user_badges = []
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
                new_user_badges.append(new_ub)
                is_unlocked = True
                unlocked_at = datetime.datetime.utcnow()

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

    if new_user_badges:
        db.add_all(new_user_badges)
        db.commit()

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

@router.get("/analytics/learning-health", response_model=LearningHealthOut)
def get_learning_health_score(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Computes an objective, pedagogical Learning Health Indicator.
    Derived from: topic mastery, spaced repetition review adherence, and study streak consistency.
    (Purely an educational health index, not mental-health related).
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    attempts = db.query(QuizAttempt).filter(QuizAttempt.student_user_id == current_user.id).all()
    schedules = db.query(SpacedRepetitionSchedule).filter(SpacedRepetitionSchedule.student_user_id == current_user.id).all()

    # 1. Accuracy component (0 to 40 pts)
    if not attempts:
        return LearningHealthOut(
            student_id=current_user.id,
            learning_health_score=0,
            status_label="Insufficient Data",
            mastery_index=0.0,
            streak_days=profile.streak_count if profile else 0,
            revision_consistency_rate=1.0,
            weak_topics_count=0,
            summary_insight="Complete at least 2 quizzes to establish an initial diagnostic learning baseline."
        )

    avg_accuracy = sum(float(a.accuracy_percentage) for a in attempts) / len(attempts)
    accuracy_pts = (avg_accuracy / 100.0) * 40.0

    # 2. Spaced review consistency component (0 to 30 pts)
    today = datetime.date.today()
    overdue_count = sum(1 for s in schedules if s.next_review_date < today)
    total_scheds = max(1, len(schedules))
    review_rate = max(0.0, 1.0 - (overdue_count / total_scheds))
    review_pts = review_rate * 30.0

    # 3. Habit / Streak component (0 to 30 pts)
    streak = profile.streak_count if profile else 0
    streak_pts = min(30.0, streak * 5.0 + 10.0)

    total_health = int(round(accuracy_pts + review_pts + streak_pts))
    total_health = max(10, min(100, total_health))

    if total_health >= 80:
        label = "Strong Progress"
        insight = "High retention, consistent study habit, and solid quiz accuracy."
    elif total_health >= 60:
        label = "Steady & Consistent"
        insight = "Good progress. Reviewing upcoming flashcards will strengthen mastery."
    else:
        label = "Needs Reinforcement"
        insight = "Focus on scheduled revision topics and foundational practice to build confidence."

    weak_count = sum(1 for a in attempts if float(a.accuracy_percentage) < 60.0)

    return LearningHealthOut(
        student_id=current_user.id,
        learning_health_score=total_health,
        status_label=label,
        mastery_index=round(avg_accuracy / 100.0, 2),
        streak_days=streak,
        revision_consistency_rate=round(review_rate, 2),
        weak_topics_count=weak_count,
        summary_insight=insight
    )
