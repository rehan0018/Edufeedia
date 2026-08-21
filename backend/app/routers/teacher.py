from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import datetime

from app.database import get_db
from app.models.models import (
    User, SchoolClass, StudentProfile, StudentProgress, QuizAttempt,
    Quiz, Question, ClassAssignment, teacher_classes
)
from app.schemas.schemas import (
    TeacherClassOut, ClassAnalyticsOut, StudentRosterItem,
    QuizCreateRequest, QuizOut, ClassAssignmentCreate, ClassAssignmentOut
)
from app.core.security import RoleChecker

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.get("/classes", response_model=List[TeacherClassOut])
def get_teacher_classes(
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    # Query classes linked to this teacher
    class_links = db.query(teacher_classes).filter(
        teacher_classes.c.teacher_user_id == current_user.id
    ).all()
    
    results = []
    for link in class_links:
        school_class = db.query(SchoolClass).filter(SchoolClass.id == link.class_id).first()
        if school_class:
            student_count = db.query(StudentProfile).filter(StudentProfile.class_id == school_class.id).count()
            results.append(TeacherClassOut(
                class_id=school_class.id,
                grade_level=school_class.grade_level,
                section_name=school_class.section_name,
                academic_year=school_class.academic_year,
                subject=link.subject,
                student_count=student_count
            ))
            
    return results

from app.core.access_policy import AccessPolicy

@router.get("/classes/{class_id}/analytics", response_model=ClassAnalyticsOut)
def get_class_analytics(
    class_id: str,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    school_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="School class not found")

    # Tenant & Class Isolation: Ensure teacher/admin is authorized for this specific class
    if not AccessPolicy.can_manage_class(current_user, class_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to access analytics for this class or school tenant."
        )

    profiles = db.query(StudentProfile).filter(StudentProfile.class_id == class_id).all()
    
    roster = []
    total_class_acc = 0.0
    total_class_lessons = 0
    at_risk_count = 0

    for prof in profiles:
        student_user = prof.user
        attempts = db.query(QuizAttempt).filter(QuizAttempt.student_user_id == student_user.id).all()
        avg_acc = 0.0
        if attempts:
            avg_acc = float(sum(a.accuracy_percentage for a in attempts) / len(attempts))
        
        completed_lessons = db.query(StudentProgress).filter(
            StudentProgress.student_user_id == student_user.id,
            StudentProgress.progress_percentage == 100
        ).count()

        is_at_risk = (avg_acc < 70.0 and len(attempts) > 0) or (prof.streak_count == 0 and len(attempts) > 0)
        if is_at_risk:
            at_risk_count += 1

        total_class_acc += avg_acc
        total_class_lessons += completed_lessons

        roster.append(StudentRosterItem(
            student_id=student_user.id,
            name=f"{student_user.first_name} {student_user.last_name}",
            email=student_user.email,
            xp=prof.xp_score,
            streak=prof.streak_count,
            average_accuracy=round(avg_acc, 1),
            lessons_completed=completed_lessons,
            is_at_risk=is_at_risk
        ))

    class_avg = round(total_class_acc / len(profiles), 1) if profiles else 0.0

    return ClassAnalyticsOut(
        class_id=school_class.id,
        grade_level=school_class.grade_level,
        section_name=school_class.section_name,
        total_students=len(profiles),
        class_average_accuracy=class_avg,
        average_mastery_percentage=class_avg,
        total_lessons_completed=total_class_lessons,
        at_risk_students_count=at_risk_count,
        students=roster
    )

@router.post("/quizzes", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_in: QuizCreateRequest,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    if not quiz_in.questions:
        raise HTTPException(status_code=400, detail="Quiz must contain at least one question")

    quiz = Quiz(
        title=quiz_in.title,
        content_item_id=quiz_in.content_item_id
    )
    db.add(quiz)
    db.flush()

    for q in quiz_in.questions:
        question = Question(
            quiz_id=quiz.id,
            question_text=q.question_text,
            options=q.options,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            difficulty=q.difficulty
        )
        db.add(question)

    db.commit()
    db.refresh(quiz)
    return quiz

@router.post("/assignments", response_model=ClassAssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_in: ClassAssignmentCreate,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    # Verify the teacher is authorized to post to this class
    if not AccessPolicy.can_manage_class(current_user, assignment_in.class_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to create assignments for this class."
        )

    assignment = ClassAssignment(
        teacher_user_id=current_user.id,
        class_id=assignment_in.class_id,
        content_item_id=assignment_in.content_item_id,
        quiz_id=assignment_in.quiz_id,
        title=assignment_in.title,
        instructions=assignment_in.instructions,
        due_date=assignment_in.due_date
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/assignments/{class_id}", response_model=List[ClassAssignmentOut])
def get_class_assignments(
    class_id: str,
    current_user: User = Depends(RoleChecker(["teacher", "student", "school_admin"])),
    db: Session = Depends(get_db)
):
    # If student, verify enrollment in class
    if current_user.role == "student":
        sp = current_user.student_profile
        if not sp or sp.class_id != class_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not enrolled in this class."
            )
    elif not AccessPolicy.can_manage_class(current_user, class_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to view assignments for this class."
        )

    return db.query(ClassAssignment).filter(ClassAssignment.class_id == class_id).order_by(ClassAssignment.created_at.desc()).all()
