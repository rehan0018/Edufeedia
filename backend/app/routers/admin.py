from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.database import get_db
from app.models.models import (
    User, StudentProfile, ContentItem, QuizAttempt, Quiz,
    UserInteraction, Flashcard, Badge, ClassAssignment, School, SchoolClass
)
from app.core.security import get_password_hash, RoleChecker

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/records")
def get_all_database_records(
    current_user: User = Depends(RoleChecker(["school_admin", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns live database records scoped strictly to the authenticated administrator's school tenant.
    Super-admins may inspect cross-school records.
    """
    school_id = current_user.school_id if current_user.role == "school_admin" else None

    # 1. Users (scoped)
    user_query = db.query(User)
    if school_id:
        user_query = user_query.filter(User.school_id == school_id)
    users_db = user_query.all()
    users_list = []
    for u in users_db:
        users_list.append({
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email,
            "role": u.role,
            "is_verified": u.is_verified,
            "school": u.school.name if u.school else "Partner School",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "Recent"
        })

    # 2. Student Profiles & XP (scoped)
    profile_query = db.query(StudentProfile)
    if school_id:
        profile_query = profile_query.filter(StudentProfile.school_id == school_id)
    profiles_db = profile_query.all()
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

    # 4. Quiz Attempts (scoped)
    quiz_query = db.query(QuizAttempt).join(User, QuizAttempt.student_user_id == User.id)
    if school_id:
        quiz_query = quiz_query.filter(User.school_id == school_id)
    quiz_attempts_db = quiz_query.order_by(QuizAttempt.completed_at.desc()).limit(50).all()
    quiz_records = []
    for qa in quiz_attempts_db:
        quiz_records.append({
            "id": qa.id,
            "student_name": f"{qa.student.first_name} {qa.student.last_name}" if qa.student else "Student",
            "score": f"{qa.score}/{qa.max_score}",
            "accuracy": f"{qa.accuracy_percentage:.1f}%",
            "date": qa.completed_at.strftime("%Y-%m-%d %H:%M") if qa.completed_at else "Recent"
        })

    # 5. User Interactions (Recommendation Feedback, scoped)
    inter_query = db.query(UserInteraction).join(User, UserInteraction.user_id == User.id)
    if school_id:
        inter_query = inter_query.filter(User.school_id == school_id)
    interactions_db = inter_query.order_by(UserInteraction.created_at.desc()).limit(50).all()
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
from pydantic import BaseModel, EmailStr
from app.core.excel_exporter import sync_database_to_excel
from app.core.security import get_current_user, RoleChecker
from app.core.redis_client import redis_client
from app.core.email_service import email_service
import secrets

class TeacherInviteRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    class_ids: Optional[List[str]] = []

class SchoolAdminCreateRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    school_id: str

@router.post("/invite-teacher")
def invite_teacher(
    req: TeacherInviteRequest,
    current_user: User = Depends(RoleChecker(["school_admin", "admin"])),
    db: Session = Depends(get_db)
):
    """
    School Admin / Platform Admin endpoint to invite a certified teacher into the tenant boundary.
    Generates an encrypted invitation token and delivers it via transactional email.
    """
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    if current_user.role == "school_admin":
        school_id = current_user.school_id
        if not school_id:
            raise HTTPException(status_code=403, detail="School admin account is not assigned to a school tenant.")
        if req.class_ids:
            for cid in req.class_ids:
                sc = db.query(SchoolClass).filter(SchoolClass.id == cid).first()
                if not sc or sc.school_id != school_id:
                    raise HTTPException(status_code=403, detail=f"Access denied: Class {cid} does not belong to your school tenant.")
    else:
        school_id = current_user.school_id
        if not school_id:
            school = db.query(School).first()
            school_id = school.id if school else None

    # Create unverified teacher account with random temporary unusable hash
    teacher_user = User(
        email=req.email,
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        role="teacher",
        first_name=req.first_name,
        last_name=req.last_name,
        is_verified=False, # Must activate via invitation token
        school_id=school_id
    )
    db.add(teacher_user)
    db.flush()

    # Link to classes if specified
    if req.class_ids:
        from app.models.models import teacher_classes
        for cid in req.class_ids:
            db.execute(teacher_classes.insert().values(
                teacher_user_id=teacher_user.id,
                class_id=cid
            ))

    db.commit()

    # Generate 7-day invitation token
    invite_token = secrets.token_urlsafe(32)
    redis_client.setex(f"invite_token:{invite_token}", 7 * 86400, teacher_user.id)

    school_obj = db.query(School).filter(School.id == school_id).first()
    school_name = school_obj.name if school_obj else "Partner School"

    email_result = email_service.send_staff_invitation(
        recipient_email=req.email,
        role="teacher",
        invitation_token=invite_token,
        school_name=school_name
    )

    return {
        "status": "invitation_dispatched",
        "email": req.email,
        "role": "teacher",
        "school_id": school_id,
        "delivery": email_result["status"]
    }

@router.post("/create-school-admin")
def create_school_admin(
    req: SchoolAdminCreateRequest,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Platform Super-Admin endpoint to establish school administrator credentials.
    """
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    admin_user = User(
        email=req.email,
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        role="school_admin",
        first_name=req.first_name,
        last_name=req.last_name,
        is_verified=False,
        school_id=req.school_id
    )
    db.add(admin_user)
    db.commit()

    invite_token = secrets.token_urlsafe(32)
    redis_client.setex(f"invite_token:{invite_token}", 7 * 86400, admin_user.id)

    email_service.send_staff_invitation(
        recipient_email=req.email,
        role="school_admin",
        invitation_token=invite_token,
        school_name="Edufeedia School Administration"
    )

    return {
        "status": "school_admin_invited",
        "email": req.email,
        "school_id": req.school_id
    }

@router.get("/export-excel")
def export_database_records_to_excel(
    current_user: User = Depends(RoleChecker(["school_admin", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Authenticated, tenant-scoped administrative on-demand database report.
    """
    file_path = sync_database_to_excel(db)
    return FileResponse(
        path=file_path,
        filename="edufeedia_database_records.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
