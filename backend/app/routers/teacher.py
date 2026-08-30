from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import datetime

from app.database import get_db
from app.models.models import (
    User, SchoolClass, StudentProfile, StudentProgress, QuizAttempt,
    Quiz, Question, ClassAssignment, teacher_classes, ContentReport, ContentItem, SpacedRepetitionSchedule
)
from app.schemas.schemas import (
    TeacherClassOut, ClassAnalyticsOut, StudentRosterItem,
    QuizCreateRequest, QuizOut, ClassAssignmentCreate, ClassAssignmentOut,
    ContentReportOut, ContentReportReview, TeacherInterventionItem, TeacherInterventionsResponse
)
from app.core.security import RoleChecker
from app.core.access_policy import AccessPolicy

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

    if quiz_in.content_item_id:
        item = db.query(ContentItem).filter(ContentItem.id == quiz_in.content_item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Referenced curriculum content not found")
        if item.school_id and item.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot create assessments for content belonging to another school."
            )

    quiz = Quiz(
        title=quiz_in.title,
        content_item_id=quiz_in.content_item_id,
        school_id=current_user.school_id
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

@router.get("/interventions", response_model=TeacherInterventionsResponse)
def get_teacher_interventions(
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Teacher Intervention Engine:
    Scans assigned classrooms to detect students struggling with accuracy (<60%),
    missed spaced repetition reviews, or weak prerequisite topics.
    """
    # 1. Get assigned class IDs
    if current_user.role == "school_admin":
        classes = db.query(SchoolClass).filter(SchoolClass.school_id == current_user.school_id).all()
    else:
        assigned_links = db.query(teacher_classes).filter(teacher_classes.c.teacher_user_id == current_user.id).all()
        class_ids = [l.class_id for l in assigned_links]
        classes = db.query(SchoolClass).filter(SchoolClass.id.in_(class_ids)).all() if class_ids else []

    interventions: List[TeacherInterventionItem] = []

    for sc in classes:
        students = db.query(StudentProfile).filter(StudentProfile.class_id == sc.id).all()
        for sp in students:
            student_user = db.query(User).filter(User.id == sp.user_id).first()
            if not student_user:
                continue

            name = f"{student_user.first_name} {student_user.last_name}"

            # Check recent quiz attempts
            recent_attempts = db.query(QuizAttempt).filter(
                QuizAttempt.student_user_id == student_user.id
            ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()

            if recent_attempts:
                low_score_attempts = [a for a in recent_attempts if float(a.accuracy_percentage) < 60.0]
                if len(low_score_attempts) >= 2:
                    interventions.append(TeacherInterventionItem(
                        student_id=student_user.id,
                        student_name=name,
                        class_id=sc.id,
                        grade_level=sc.grade_level,
                        section_name=sc.section_name,
                        severity="high",
                        reason="Repeated Low Quiz Accuracy (<60%)",
                        recommended_action="Assign targeted diagnostic flashcard deck and foundational revision lesson."
                    ))

            # Check Topic Mastery deficiencies
            from app.models.models import TopicMastery
            weak_masteries = db.query(TopicMastery).filter(
                TopicMastery.student_user_id == student_user.id,
                (TopicMastery.mastery_score < 55) | (TopicMastery.trend == "declining")
            ).all()

            for wt in weak_masteries:
                interventions.append(TeacherInterventionItem(
                    student_id=student_user.id,
                    student_name=name,
                    class_id=sc.id,
                    grade_level=sc.grade_level,
                    section_name=sc.section_name,
                    severity="high" if (wt.mastery_score or 0) < 40 else "medium",
                    reason=f"Deficiency in {wt.topic} (Mastery: {float(wt.mastery_score):.0f}%, Trend: {wt.trend})",
                    recommended_action=f"Assign foundational lesson in {wt.subject} — {wt.topic}."
                ))

            # Check missed spaced reviews
            overdue_reviews = db.query(SpacedRepetitionSchedule).filter(
                SpacedRepetitionSchedule.student_user_id == student_user.id,
                SpacedRepetitionSchedule.next_review_date < datetime.date.today()
            ).count()

            if overdue_reviews >= 3:
                interventions.append(TeacherInterventionItem(
                    student_id=student_user.id,
                    student_name=name,
                    class_id=sc.id,
                    grade_level=sc.grade_level,
                    section_name=sc.section_name,
                    severity="medium",
                    reason=f"{overdue_reviews} Overdue Spaced Repetition Reviews",
                    recommended_action="Encourage daily 5-minute memory retention review cycle."
                ))

    high_count = sum(1 for i in interventions if i.severity == "high")
    return TeacherInterventionsResponse(
        total_interventions=len(interventions),
        high_urgency_count=high_count,
        interventions=interventions
    )

@router.get("/moderation-queue", response_model=List[ContentReportOut])
def get_moderation_queue(
    current_user: User = Depends(RoleChecker(["teacher", "school_admin", "admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """
    Retrieves pending student/parent content reports for pedagogical & safety moderation.
    Strictly tenant-scoped for teachers and school administrators.
    """
    query = db.query(ContentReport).join(ContentItem, ContentReport.content_item_id == ContentItem.id).filter(
        ContentReport.status == "pending_review"
    )

    if current_user.role in ["teacher", "school_admin"]:
        school_id = current_user.school_id
        if school_id:
            # Teacher / School Admin only sees reports for items tied to their school or reported by their students
            query = query.join(User, ContentReport.reporter_user_id == User.id).filter(
                (ContentItem.school_id == school_id) | (User.school_id == school_id)
            )
        else:
            query = query.filter(ContentItem.school_id == None)

    reports = query.order_by(ContentReport.created_at.desc()).all()
    results = []
    for r in reports:
        item = db.query(ContentItem).filter(ContentItem.id == r.content_item_id).first()
        results.append(ContentReportOut(
            id=r.id,
            content_item_id=r.content_item_id,
            content_title=item.title if item else "Unknown Resource",
            reporter_id=r.reporter_user_id,
            reason=r.reason,
            details=r.details,
            status=r.status,
            created_at=r.created_at
        ))
    return results

@router.post("/moderate-report", response_model=ContentReportOut)
def moderate_report(
    review: ContentReportReview,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin", "admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """
    Resolves or dismisses a student/parent content report with strict tenant authorization.
    """
    report = db.query(ContentReport).filter(ContentReport.id == review.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Content report not found")

    item = db.query(ContentItem).filter(ContentItem.id == report.content_item_id).first()
    reporter = db.query(User).filter(User.id == report.reporter_user_id).first()

    # Tenant validation
    if current_user.role in ["teacher", "school_admin"]:
        is_same_item_school = (item and item.school_id == current_user.school_id)
        is_same_reporter_school = (reporter and reporter.school_id == current_user.school_id)
        if not (is_same_item_school or is_same_reporter_school or (item and item.school_id is None)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to moderate reports from another school."
            )

    report.status = review.status
    report.action_taken = review.action_taken
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(report)

    return ContentReportOut(
        id=report.id,
        content_item_id=report.content_item_id,
        content_title=item.title if item else "Unknown Resource",
        reporter_id=report.reporter_user_id,
        reason=report.reason,
        details=report.details,
        status=report.status,
        created_at=report.created_at
    )
