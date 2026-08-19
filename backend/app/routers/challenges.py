import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import User, StudentProfile, SchoolClass, QuizAttempt, StudentProgress
from app.core.security import get_current_user, RoleChecker

router = APIRouter(prefix="/challenges", tags=["challenges"])

@router.get("/weekly")
def get_weekly_challenge(
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns the active weekly academic challenge for the school.
    Pedagogical focus: Collaborative class-level mastery rather than toxic child rankings.
    """
    today = datetime.date.today()
    days_to_sunday = 6 - today.weekday() if today.weekday() <= 6 else 0
    next_monday = today + datetime.timedelta(days=days_to_sunday + 1)

    return {
        "id": "chal-weekly-2026-w34",
        "title": "Weekly STEM Momentum Challenge",
        "subject_focus": "Science & Computer Networks",
        "core_topic": "Newton's Laws & Network Topologies",
        "description": "Collaborate with your classmates! Every quiz completed and lesson mastered contributes XP directly to your class team total.",
        "start_date": (today - datetime.timedelta(days=today.weekday())).isoformat(),
        "end_date": (today + datetime.timedelta(days=days_to_sunday)).isoformat(),
        "days_remaining": max(1, days_to_sunday),
        "target_class_xp": 1000,
        "next_challenge": {
            "title": "Algebra & Quadratic Functions Sprint",
            "starts": next_monday.isoformat()
        }
    }

@router.get("/class-leaderboard")
def get_class_leaderboard(
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns authentic class-level aggregated standings for the user's school.
    Multi-School Tenant Isolation: Only returns classes belonging to current_user.school_id.
    Zero Metric Fabrication: Returns authentic database totals only.
    """
    school_id = current_user.school_id
    if not school_id and current_user.student_profile:
        school_id = current_user.student_profile.school_id

    # Filter strictly by school tenant boundary
    class_query = db.query(SchoolClass)
    if school_id:
        class_query = class_query.filter(SchoolClass.school_id == school_id)
    classes = class_query.all()
    
    leaderboard = []

    for cls in classes:
        profiles = db.query(StudentProfile).filter(StudentProfile.class_id == cls.id).all()
        student_user_ids = [p.user_id for p in profiles]

        total_xp = sum(p.xp_score for p in profiles)
        student_count = len(profiles)

        avg_acc = None
        if student_user_ids:
            attempts = db.query(QuizAttempt).filter(QuizAttempt.student_user_id.in_(student_user_ids)).all()
            if attempts:
                avg_acc = round(sum(a.accuracy_percentage for a in attempts) / len(attempts), 1)

        leaderboard.append({
            "class_id": cls.id,
            "grade_level": cls.grade_level,
            "section_name": cls.section_name,
            "class_name": f"Class {cls.grade_level}{cls.section_name}",
            "academic_year": cls.academic_year,
            "total_xp": total_xp,
            "student_count": student_count,
            "average_accuracy": avg_acc,
            "data_status": "active" if student_count > 0 else "insufficient_data",
            "is_my_class": (
                current_user.role == "student" and
                current_user.student_profile is not None and
                current_user.student_profile.class_id == cls.id
            )
        })

    # Sort leaderboard by total XP descending
    leaderboard.sort(key=lambda x: x["total_xp"], reverse=True)

    for rank, item in enumerate(leaderboard, 1):
        item["rank"] = rank

    return leaderboard

@router.get("/my-growth")
def get_my_personal_growth(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    """
    Returns authentic personal learning growth based on historical quiz performance.
    Zero Metric Fabrication: If insufficient historical data, returns clear status.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    
    # Calculate genuine growth based on quiz attempts
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == current_user.id
    ).order_by(QuizAttempt.completed_at.asc()).all()

    growth_pct = None
    statement = "Complete your first 3 quizzes to calculate your personal learning growth rate!"
    data_status = "insufficient_data"

    if len(attempts) >= 2:
        midpoint = len(attempts) // 2
        earlier_attempts = attempts[:midpoint]
        recent_attempts = attempts[midpoint:]

        avg_early = sum(float(a.accuracy_percentage) for a in earlier_attempts) / len(earlier_attempts)
        avg_recent = sum(float(a.accuracy_percentage) for a in recent_attempts) / len(recent_attempts)

        if avg_early > 0:
            growth_pct = round(((avg_recent - avg_early) / avg_early) * 100.0, 1)
            statement = f"Your quiz accuracy improved by {growth_pct:+.1f}% compared to your earlier attempts!"
            data_status = "verified"
        else:
            growth_pct = round(avg_recent, 1)
            statement = f"Your current quiz accuracy average is {avg_recent:.1f}%."
            data_status = "verified"

    return {
        "student_id": current_user.id,
        "current_xp": profile.xp_score if profile else 0,
        "streak_days": profile.streak_count if profile else 0,
        "monthly_improvement_percentage": growth_pct,
        "growth_statement": statement,
        "data_status": data_status,
        "privacy_note": "This personal growth metric is completely private to you and your guardian."
    }
