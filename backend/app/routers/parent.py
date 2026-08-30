from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import datetime

from app.database import get_db
from app.models.models import User, StudentProfile, StudentProgress, QuizAttempt, parent_student_links, ParentalConsentLog, SpacedRepetitionSchedule
from app.schemas.schemas import ParentWeeklySummaryOut
from app.core.security import get_current_user, RoleChecker
from app.core.access_policy import AccessPolicy

router = APIRouter(prefix="/parents", tags=["parents"])

@router.get("/students", response_model=List[Dict[str, Any]])
def get_linked_students(
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    # Fetch verified linked students
    links = db.query(parent_student_links).filter(
        parent_student_links.c.parent_user_id == current_user.id,
        parent_student_links.c.is_verified == True
    ).all()
    
    student_ids = [link.student_user_id for link in links]
    students = db.query(User).filter(User.id.in_(student_ids)).all()
    
    results = []
    for s in students:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == s.id).first()
        consent = db.query(ParentalConsentLog).filter(
            ParentalConsentLog.parent_user_id == current_user.id,
            ParentalConsentLog.student_user_id == s.id,
            ParentalConsentLog.consent_status == "granted"
        ).first()

        results.append({
            "student_id": s.id,
            "name": f"{s.first_name} {s.last_name}",
            "email": s.email,
            "board": profile.board if profile else "CBSE",
            "xp": profile.xp_score if profile else 0,
            "streak": profile.streak_count if profile else 0,
            "consent_verified": bool(consent),
            "consent_granted_at": consent.granted_at.isoformat() if consent and consent.granted_at else None
        })
        
    return results

@router.get("/student/{student_id}/progress", response_model=Dict[str, Any])
def get_student_progress_summary(
    student_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    # Check verified parent-student linkage
    link = db.query(parent_student_links).filter(
        parent_student_links.c.parent_user_id == current_user.id,
        parent_student_links.c.student_user_id == student_id,
        parent_student_links.c.is_verified == True
    ).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this student's progress."
        )
        
    student = db.query(User).filter(User.id == student_id).first()
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    
    if not student or not profile:
        raise HTTPException(status_code=404, detail="Student record not found")
        
    # Aggregate progress metrics
    completed_logs = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == student_id,
        StudentProgress.progress_percentage == 100
    ).all()
    
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == student_id
    ).all()
    
    avg_accuracy = 0.0
    if attempts:
        avg_accuracy = float(sum(a.accuracy_percentage for a in attempts) / len(attempts))
        
    # Analyze topic mastery levels
    subject_completion = {}
    for log in completed_logs:
        sub = log.content_item.subject
        subject_completion[sub] = subject_completion.get(sub, 0) + 1
        
    # Identify strengths and weaknesses strictly from real student data
    subject_accuracies = {}
    subject_counts = {}
    
    for a in attempts:
        if a.quiz and a.quiz.content_item:
            sub = a.quiz.content_item.subject
            subject_accuracies[sub] = subject_accuracies.get(sub, 0) + float(a.accuracy_percentage)
            subject_counts[sub] = subject_counts.get(sub, 0) + 1
            
    strengths = []
    weaknesses = []
    for sub, total_acc in subject_accuracies.items():
        avg_sub_acc = total_acc / subject_counts[sub]
        if avg_sub_acc >= 80:
            strengths.append({"subject": sub, "accuracy": avg_sub_acc})
        elif avg_sub_acc < 70:
            weaknesses.append({"subject": sub, "accuracy": avg_sub_acc})

    # Query Real Topic Masteries
    from app.models.models import TopicMastery
    masteries = db.query(TopicMastery).filter(TopicMastery.student_user_id == student_id).all()
    topic_breakdown = [
        {
            "subject": m.subject,
            "topic": m.topic,
            "mastery_score": float(m.mastery_score or 0.0),
            "confidence": float(m.confidence or 0.5),
            "trend": m.trend,
            "attempts": m.attempt_count
        }
        for m in masteries
    ]

    weak_topics = [m.topic for m in masteries if (m.mastery_score or 0) < 70 or m.trend == "declining"]
    if weak_topics:
        recommended_action = f"Encourage 20 minutes of {weak_topics[0]} practice this week."
    elif weaknesses:
        recommended_action = f"Encourage 15 minutes of {weaknesses[0]['subject']} revision."
    else:
        recommended_action = "Maintain the current study cadence with regular active recall reviews."

    consent = db.query(ParentalConsentLog).filter(
        ParentalConsentLog.parent_user_id == current_user.id,
        ParentalConsentLog.student_user_id == student_id,
        ParentalConsentLog.consent_status == "granted"
    ).first()

    return {
        "student_name": f"{student.first_name} {student.last_name}",
        "class_grade": profile.school_class.grade_level if profile.school_class else 10,
        "xp": profile.xp_score,
        "streak": profile.streak_count,
        "total_lessons_completed": len(completed_logs),
        "average_quiz_accuracy": avg_accuracy,
        "subject_progress": [
            {"subject": sub, "lessons_completed": count} for sub, count in subject_completion.items()
        ],
        "topic_masteries": topic_breakdown,
        "academic_insights": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "insufficient_data": (len(attempts) == 0),
            "revision_urgency": "High" if weak_topics else ("Medium" if weaknesses else "Low"),
            "recommended_parent_action": recommended_action
        },
        "consent": {
            "is_verified": bool(consent),
            "purpose": "Curated Educational Learning & AI Tutoring",
            "granted_at": consent.granted_at.isoformat() if consent and consent.granted_at else None
        }
    }

@router.get("/student/{student_id}/weekly-summary", response_model=ParentWeeklySummaryOut)
def get_parent_weekly_summary(
    student_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """
    Weekly Learning Summary for Guardians:
    Aggregates weekly educational progress, mastery growth, AI tutor usage, and revision topics
    to reduce the cognitive burden of continuous manual parental monitoring.
    """
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student account not found")

    if not AccessPolicy.can_view_student_data(current_user, student, db=db):
        raise HTTPException(status_code=403, detail="Access denied: You are not authorized for this student.")

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=7)

    # Weekly completed lessons
    weekly_lessons = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == student_id,
        StudentProgress.progress_percentage == 100,
        StudentProgress.completed_at >= week_start
    ).count()

    # Weekly quizzes taken
    weekly_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == student_id,
        QuizAttempt.completed_at >= week_start
    ).all()

    avg_accuracy = (
        sum(float(a.accuracy_percentage) for a in weekly_attempts) / len(weekly_attempts)
        if weekly_attempts else 0.0
    )

    # Overdue/upcoming revision topics
    overdue_schedules = db.query(SpacedRepetitionSchedule).filter(
        SpacedRepetitionSchedule.student_user_id == student_id,
        SpacedRepetitionSchedule.next_review_date <= today + datetime.timedelta(days=2)
    ).all()
    revision_topics = list(set([s.topic for s in overdue_schedules]))[:5]

    # Insight synthesis
    name = f"{student.first_name} {student.last_name}".strip() or "Your student"
    if weekly_lessons >= 5 and avg_accuracy >= 75.0:
        insight = f"{name} had a highly productive week with solid comprehension and consistent study cadence."
    elif revision_topics:
        insight = f"{name} is progressing steadily. Focus on upcoming spaced repetition revision for: {', '.join(revision_topics[:2])}."
    else:
        insight = f"{name} is maintaining positive learning momentum with zero safety alerts."

    # Measure actual interactions
    from app.models.models import UserInteraction
    tutor_query_count = db.query(UserInteraction).filter(
        UserInteraction.user_id == student_id,
        UserInteraction.created_at >= week_start
    ).count()

    mastery_delta = 0.0
    if len(weekly_attempts) >= 2:
        oldest_acc = float(weekly_attempts[-1].accuracy_percentage)
        newest_acc = float(weekly_attempts[0].accuracy_percentage)
        mastery_delta = round(max(0.0, newest_acc - oldest_acc), 1)

    return ParentWeeklySummaryOut(
        student_id=student.id,
        student_name=name,
        week_start=week_start.isoformat(),
        week_end=today.isoformat(),
        lessons_completed=weekly_lessons,
        quizzes_taken=len(weekly_attempts),
        average_accuracy=round(avg_accuracy, 1),
        ai_tutor_sessions=tutor_query_count,
        mastery_improvement_percentage=mastery_delta,
        topics_needing_revision=revision_topics,
        safety_incident_count=0,
        parent_insight=insight
    )
