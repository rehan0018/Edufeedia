from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.models.models import (
    User, StudentProfile, ContentItem, QuizAttempt, Quiz,
    UserInteraction, Flashcard, Badge, ClassAssignment, School
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/records")
def get_all_database_records(db: Session = Depends(get_db)):
    """
    Returns full, transparent live database records and table summaries for inspection.
    """
    # 1. Users
    users_db = db.query(User).all()
    users_list = []
    for u in users_db:
        users_list.append({
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email,
            "role": u.role,
            "is_verified": u.is_verified,
            "school": u.school.name if u.school else "Apex Academy",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "Recent"
        })

    # 2. Student Profiles & XP
    profiles_db = db.query(StudentProfile).all()
    student_records = []
    for sp in profiles_db:
        student_records.append({
            "user_id": sp.user_id,
            "name": f"{sp.user.first_name} {sp.user.last_name}" if sp.user else "Student",
            "email": sp.user.email if sp.user else "N/A",
            "grade": sp.school_class.grade_level if sp.school_class else 10,
            "section": sp.school_class.section_name if sp.school_class else "A",
            "board": sp.board or "CBSE",
            "xp_score": sp.xp_score,
            "streak_count": sp.streak_count,
            "interests": sp.interests or []
        })

    # 3. Content Items & Safety Scores
    content_db = db.query(ContentItem).all()
    content_list = []
    for c in content_db:
        content_list.append({
            "id": c.id,
            "title": c.title,
            "subject": c.subject,
            "topic": c.topic,
            "grade": c.grade_level,
            "board": c.board,
            "type": c.type,
            "safety_score": c.safety_score,
            "edu_score": c.edu_score,
            "views": c.view_count,
            "likes": c.like_count
        })

    # 4. Quiz Attempts
    quiz_attempts_db = db.query(QuizAttempt).order_by(QuizAttempt.completed_at.desc()).limit(20).all()
    quiz_records = []
    for qa in quiz_attempts_db:
        quiz_records.append({
            "id": qa.id,
            "student_name": f"{qa.student.first_name} {qa.student.last_name}" if qa.student else "Student",
            "score": f"{qa.score}/{qa.max_score}",
            "accuracy": f"{qa.accuracy_percentage:.1f}%",
            "date": qa.completed_at.strftime("%Y-%m-%d %H:%M") if qa.completed_at else "Recent"
        })

    # 5. User Interactions (Recommendation Feedback)
    interactions_db = db.query(UserInteraction).order_by(UserInteraction.created_at.desc()).limit(25).all()
    interaction_records = []
    for inter in interactions_db:
        interaction_records.append({
            "id": inter.id,
            "user_email": inter.user.email if inter.user else "User",
            "content_title": inter.content_item.title if inter.content_item else "Lesson",
            "interaction_type": inter.interaction_type,
            "weight": float(inter.weight),
            "dwell_time": f"{inter.dwell_time_seconds}s",
            "created_at": inter.created_at.strftime("%Y-%m-%d %H:%M") if inter.created_at else "Recent"
        })

    # 6. Flashcards
    flashcards_db = db.query(Flashcard).all()
    flashcards_list = [{
        "id": f.id,
        "subject": f.subject,
        "topic": f.topic,
        "front": f.front_text,
        "back": f.back_text,
        "hint": f.hint or ""
    } for f in flashcards_db]

    return {
        "stats": {
            "total_users": len(users_list),
            "total_students": len(student_records),
            "total_content_items": len(content_list),
            "total_quiz_attempts": len(quiz_records),
            "total_interactions_logged": len(interaction_records),
            "total_flashcards": len(flashcards_list)
        },
        "users": users_list,
        "students": student_records,
        "content_items": content_list,
        "quiz_attempts": quiz_records,
        "interactions": interaction_records,
        "flashcards": flashcards_list
    }

from fastapi.responses import FileResponse
from app.core.excel_exporter import sync_database_to_excel

@router.get("/export-excel")
def export_database_records_to_excel(db: Session = Depends(get_db)):
    """
    Exports all current SQL tables into an updated read-only multi-tab Excel spreadsheet.
    """
    file_path = sync_database_to_excel(db)
    return FileResponse(
        path=file_path,
        filename="edufeedia_database_records.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
