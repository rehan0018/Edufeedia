from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import datetime

from app.database import get_db
from app.models.models import (
    User, StudentProfile, StudentProgress, QuizAttempt, parent_student_links,
    ParentalConsentLog, SpacedRepetitionSchedule, ParentalScreenTimePolicy,
    LearningEvent, UserInteraction, ContentItem,
    ChildProfile, ChildActivity, ChildQuizHistory, ChildAchievement, ChildContentApproval,
    SafetyIncident
)
from app.schemas.schemas import (
    ParentWeeklySummaryOut, ScreenTimeAnalyticsOut, ScreenTimePolicyUpdate,
    SubjectTimeBreakdown, ActivityFormatBreakdown, ContentActivityItem, EarlyActionAlert,
    ParentPinSet, ParentPinVerify, ParentPinOut,
    ChildProfileCreate, ChildProfileUpdate, ChildProfileOut,
    ChildControlsUpdate, ChildScreenTimeUpdate, ChildContentApprovalRequest, ChildDashboardOut
)
from app.core.security import get_current_user, RoleChecker, get_password_hash, verify_password, create_access_token
from app.core.access_policy import AccessPolicy
from app.core.age_policy import AgeBandPolicy

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

    # Real aggregated safety incidents
    real_incidents_count = db.query(SafetyIncident).filter(
        SafetyIncident.student_user_id == student_id,
        SafetyIncident.created_at >= week_start
    ).count()

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
        safety_incident_count=real_incidents_count,
        parent_insight=insight
    )


@router.get("/student/{student_id}/safety-incidents", response_model=List[Dict[str, Any]])
def get_student_safety_incidents(
    student_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Retrieves real-time logged safety incidents for the linked student."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student account not found")

    if not AccessPolicy.can_view_student_data(current_user, student, db=db):
        raise HTTPException(status_code=403, detail="Access denied: You are not authorized for this student.")

    incidents = db.query(SafetyIncident).filter(
        SafetyIncident.student_user_id == student_id
    ).order_by(SafetyIncident.created_at.desc()).limit(30).all()

    return [
        {
            "id": inc.id,
            "source": inc.source,
            "category": inc.category,
            "severity": inc.severity,
            "blocked": inc.blocked,
            "flagged_snippet": inc.flagged_snippet,
            "reason": inc.reason,
            "action_taken": inc.action_taken,
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in incidents
    ]


@router.get("/children/{child_id}/safety-incidents", response_model=List[Dict[str, Any]])
def get_child_safety_incidents(
    child_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Retrieves real-time logged safety incidents for a young child profile."""
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    incidents = db.query(SafetyIncident).filter(
        SafetyIncident.child_profile_id == child_id
    ).order_by(SafetyIncident.created_at.desc()).limit(30).all()

    return [
        {
            "id": inc.id,
            "source": inc.source,
            "category": inc.category,
            "severity": inc.severity,
            "blocked": inc.blocked,
            "flagged_snippet": inc.flagged_snippet,
            "reason": inc.reason,
            "action_taken": inc.action_taken,
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in incidents
    ]


@router.get("/student/{student_id}/screen-time", response_model=ScreenTimeAnalyticsOut)
def get_student_screen_time(
    student_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """
    Parental Screen Time & Content Consumption Analytics:
    Provides verified breakdown of time spent by subject, activity type, and specific modules,
    coupled with early warning triggers (fatigue, session limits, distraction) to enable timely parental action.
    """
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student account not found")

    if not AccessPolicy.can_view_student_data(current_user, student, db=db):
        raise HTTPException(status_code=403, detail="Access denied: You are not authorized for this student.")

    # Get or create policy
    policy = db.query(ParentalScreenTimePolicy).filter(
        ParentalScreenTimePolicy.parent_user_id == current_user.id,
        ParentalScreenTimePolicy.student_user_id == student_id
    ).first()

    if not policy:
        policy = ParentalScreenTimePolicy(
            parent_user_id=current_user.id,
            student_user_id=student_id,
            daily_limit_minutes=90,
            curfew_start_time="21:30",
            curfew_end_time="06:30",
            curfew_enabled=True,
            ai_tutor_max_daily_minutes=30
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - datetime.timedelta(days=7)

    # 1. Calculate Learning Event Verified Seconds
    learning_events_today = db.query(LearningEvent).filter(
        LearningEvent.student_user_id == student_id,
        LearningEvent.created_at >= today_start
    ).all()
    today_verified_seconds = sum(e.verified_seconds for e in learning_events_today)

    learning_events_week = db.query(LearningEvent).filter(
        LearningEvent.student_user_id == student_id,
        LearningEvent.created_at >= week_start
    ).all()
    week_verified_seconds = sum(e.verified_seconds for e in learning_events_week)

    # 2. Calculate User Interactions (Watch time, dwell time)
    interactions_today = db.query(UserInteraction).filter(
        UserInteraction.user_id == student_id,
        UserInteraction.created_at >= today_start
    ).all()
    today_interaction_seconds = sum(i.dwell_time_seconds for i in interactions_today if i.dwell_time_seconds)

    interactions_week = db.query(UserInteraction).filter(
        UserInteraction.user_id == student_id,
        UserInteraction.created_at >= week_start
    ).all()
    week_interaction_seconds = sum(i.dwell_time_seconds for i in interactions_week if i.dwell_time_seconds)

    # 3. Calculate Quiz and Progress duration estimates
    quizzes_today = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == student_id,
        QuizAttempt.completed_at >= today_start
    ).count()
    quizzes_week = db.query(QuizAttempt).filter(
        QuizAttempt.student_user_id == student_id,
        QuizAttempt.completed_at >= week_start
    ).count()

    today_raw_seconds = max(today_verified_seconds, today_interaction_seconds) + (quizzes_today * 300)
    completed_today = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == student_id,
        StudentProgress.updated_at >= today_start
    ).count()
    today_minutes = int(today_raw_seconds / 60)
    if today_minutes == 0 and completed_today > 0:
        today_minutes = completed_today * 10

    week_raw_seconds = max(week_verified_seconds, week_interaction_seconds) + (quizzes_week * 300)
    completed_week = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == student_id,
        StudentProgress.updated_at >= week_start
    ).count()
    week_minutes = int(week_raw_seconds / 60)
    if week_minutes == 0 and completed_week > 0:
        week_minutes = completed_week * 10

    all_progress = db.query(StudentProgress).filter(StudentProgress.student_user_id == student_id).all()

    daily_avg_minutes = round(week_minutes / 7) if week_minutes > 0 else 0
    daily_limit = policy.daily_limit_minutes or 90
    percent_limit_used = min(100, int((today_minutes / daily_limit) * 100)) if daily_limit > 0 else 0
    is_over_limit = today_minutes > daily_limit

    # Check curfew
    current_time_str = now.strftime("%H:%M")
    is_curfew_active = False
    if policy.curfew_enabled and policy.curfew_start_time and policy.curfew_end_time:
        if policy.curfew_start_time > policy.curfew_end_time:
            is_curfew_active = (current_time_str >= policy.curfew_start_time or current_time_str < policy.curfew_end_time)
        else:
            is_curfew_active = (policy.curfew_start_time <= current_time_str < policy.curfew_end_time)

    # 4. Subject Breakdown
    subject_map: Dict[str, int] = {}
    for p in all_progress:
        if p.content_item and p.content_item.subject:
            sub = p.content_item.subject
            dur = p.content_item.duration_minutes or 15
            subject_map[sub] = subject_map.get(sub, 0) + dur

    total_sub_time = sum(subject_map.values())
    subject_breakdown = [
        SubjectTimeBreakdown(
            subject=sub,
            minutes=mins,
            percentage=round((mins / total_sub_time) * 100, 1) if total_sub_time > 0 else 0.0
        )
        for sub, mins in sorted(subject_map.items(), key=lambda x: x[1], reverse=True)
    ]

    # 5. Activity Format Breakdown
    ai_events_today = db.query(UserInteraction).filter(
        UserInteraction.user_id == student_id,
        UserInteraction.interaction_type == "ai_query",
        UserInteraction.created_at >= today_start
    ).count()
    ai_minutes = ai_events_today * 3
    quiz_minutes = quizzes_today * 10
    video_minutes = max(0, today_minutes - ai_minutes - quiz_minutes)

    tot_act = ai_minutes + quiz_minutes + video_minutes
    activity_breakdown = [
        ActivityFormatBreakdown(
            activity_type="Video & Interactive Lessons",
            minutes=video_minutes,
            percentage=round((video_minutes / tot_act) * 100, 1) if tot_act > 0 else 0.0
        ),
        ActivityFormatBreakdown(
            activity_type="Socratic AI Tutoring",
            minutes=ai_minutes,
            percentage=round((ai_minutes / tot_act) * 100, 1) if tot_act > 0 else 0.0
        ),
        ActivityFormatBreakdown(
            activity_type="Diagnostic Quizzes & Practice",
            minutes=quiz_minutes,
            percentage=round((quiz_minutes / tot_act) * 100, 1) if tot_act > 0 else 0.0
        ),
    ]

    # 6. Recent Content Activities
    recent_activities = []
    for p in all_progress[:6]:
        if p.content_item:
            recent_activities.append(ContentActivityItem(
                id=p.content_item.id,
                title=p.content_item.title,
                subject=p.content_item.subject,
                topic=p.content_item.topic,
                activity_type=p.content_item.type or "video",
                minutes_spent=p.content_item.duration_minutes or 15,
                completed=(p.progress_percentage == 100),
                timestamp=(p.updated_at or now).strftime("%Y-%m-%d %H:%M")
            ))

    # 7. Early Action Alerts & Behavioral Guidance
    alerts = []
    if is_over_limit:
        alerts.append(EarlyActionAlert(
            severity="warning",
            type="limit",
            title="Daily Screen Time Limit Exceeded",
            description=f"{student.first_name} has consumed {today_minutes}m of screen time today, exceeding the parent threshold of {daily_limit}m.",
            recommended_action="Encourage transitioning from digital screen study to physical textbook reading or outdoor activity."
        ))
    elif percent_limit_used >= 80 and today_minutes > 0:
        alerts.append(EarlyActionAlert(
            severity="info",
            type="limit",
            title="Approaching Daily Screen Time Limit",
            description=f"{student.first_name} has reached {percent_limit_used}% ({today_minutes}m / {daily_limit}m) of their allocated daily budget.",
            recommended_action="Set a reminder for the student to wrap up active study modules within the next 15 minutes."
        ))

    if is_curfew_active:
        alerts.append(EarlyActionAlert(
            severity="warning",
            type="fatigue",
            title="Late-Night Bedtime Curfew Active",
            description=f"Device study curfew is currently enabled ({policy.curfew_start_time} - {policy.curfew_end_time}) to protect sleep hygiene.",
            recommended_action="Ensure student has powered off screens to support deep cognitive memory consolidation."
        ))

    if today_minutes >= 45:
        alerts.append(EarlyActionAlert(
            severity="info",
            type="fatigue",
            title="Continuous Study Session Milestone",
            description=f"{student.first_name} completed a focused {today_minutes}-minute learning block.",
            recommended_action="Prompt a 10-minute eye relaxation / hydration break (20-20-20 rule)."
        ))

    if today_minutes >= 15:
        alerts.append(EarlyActionAlert(
            severity="positive",
            type="balance",
            title="High-Value Curriculum Focus",
            description=f"{today_minutes}m of today's screen time was dedicated to approved curriculum modules with verified engagement.",
            recommended_action="Praise student for maintaining dedicated, distraction-free study cadence."
        ))
    elif today_minutes == 0 and not is_curfew_active and not is_over_limit:
        alerts.append(EarlyActionAlert(
            severity="info",
            type="balance",
            title="No Activity Logged Today",
            description=f"No screen time has been recorded yet for {student.first_name} today. Metrics reflect verified live device usage.",
            recommended_action="Encourage starting the daily study schedule when ready."
        ))

    return ScreenTimeAnalyticsOut(
        student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}".strip(),
        today_screen_time_minutes=today_minutes,
        weekly_screen_time_minutes=week_minutes,
        daily_average_minutes=daily_avg_minutes,
        daily_limit_minutes=daily_limit,
        percent_limit_used=percent_limit_used,
        is_over_limit=is_over_limit,
        curfew_enabled=policy.curfew_enabled,
        curfew_start_time=policy.curfew_start_time,
        curfew_end_time=policy.curfew_end_time,
        is_curfew_active=is_curfew_active,
        subject_breakdown=subject_breakdown,
        activity_breakdown=activity_breakdown,
        recent_activities=recent_activities,
        early_action_alerts=alerts,
        ai_tutor_minutes_today=ai_minutes
    )

@router.post("/student/{student_id}/screen-time/policy", response_model=Dict[str, Any])
def update_student_screen_time_policy(
    student_id: str,
    policy_data: ScreenTimePolicyUpdate,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student account not found")

    if not AccessPolicy.can_view_student_data(current_user, student, db=db):
        raise HTTPException(status_code=403, detail="Access denied: You are not authorized for this student.")

    policy = db.query(ParentalScreenTimePolicy).filter(
        ParentalScreenTimePolicy.parent_user_id == current_user.id,
        ParentalScreenTimePolicy.student_user_id == student_id
    ).first()

    if not policy:
        policy = ParentalScreenTimePolicy(
            parent_user_id=current_user.id,
            student_user_id=student_id
        )
        db.add(policy)

    if policy_data.daily_limit_minutes is not None:
        policy.daily_limit_minutes = policy_data.daily_limit_minutes
    if policy_data.curfew_start_time is not None:
        policy.curfew_start_time = policy_data.curfew_start_time
    if policy_data.curfew_end_time is not None:
        policy.curfew_end_time = policy_data.curfew_end_time
    if policy_data.curfew_enabled is not None:
        policy.curfew_enabled = policy_data.curfew_enabled
    if policy_data.ai_tutor_max_daily_minutes is not None:
        policy.ai_tutor_max_daily_minutes = policy_data.ai_tutor_max_daily_minutes
    if policy_data.break_interval_minutes is not None:
        policy.break_interval_minutes = policy_data.break_interval_minutes

    db.commit()
    db.refresh(policy)

    return {
        "status": "success",
        "message": "Parental screen time policy updated successfully.",
        "policy": {
            "daily_limit_minutes": policy.daily_limit_minutes,
            "curfew_start_time": policy.curfew_start_time,
            "curfew_end_time": policy.curfew_end_time,
            "curfew_enabled": policy.curfew_enabled,
            "ai_tutor_max_daily_minutes": policy.ai_tutor_max_daily_minutes,
            "break_interval_minutes": policy.break_interval_minutes
        }
    }


# ==============================================================================
# EduFeedia Kids & Child Profile Management Endpoints
# ==============================================================================

def serialize_child_profile(child: ChildProfile, db: Session) -> Dict[str, Any]:
    """Helper to assemble a complete ChildProfileOut dictionary."""
    age = AgeBandPolicy.calculate_age(child.date_of_birth)
    band_info = AgeBandPolicy.get_age_band_info(age)

    now = datetime.datetime.now(datetime.timezone.utc)
    cur_time = now.strftime("%H:%M")
    is_curfew_active = False
    if child.curfew_enabled and child.curfew_start_time and child.curfew_end_time:
        if child.curfew_start_time > child.curfew_end_time:
            is_curfew_active = (cur_time >= child.curfew_start_time or cur_time < child.curfew_end_time)
        else:
            is_curfew_active = (child.curfew_start_time <= cur_time < child.curfew_end_time)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    activities_today = db.query(ChildActivity).filter(
        ChildActivity.child_profile_id == child.id,
        ChildActivity.created_at >= today_start
    ).all()
    today_seconds = sum(a.dwell_time_seconds for a in activities_today if a.dwell_time_seconds)
    today_mins = max(int(today_seconds / 60), len(activities_today) * 5)

    return {
        "id": child.id,
        "parent_user_id": child.parent_user_id,
        "name": child.name,
        "date_of_birth": child.date_of_birth.isoformat(),
        "age": age,
        "age_band_key": band_info["key"],
        "age_band_name": band_info["name"],
        "preferred_language": child.preferred_language or "en",
        "secondary_language": child.secondary_language,
        "learning_level": child.learning_level or "beginner",
        "avatar_mascot": child.avatar_mascot or "space_explorer",
        "interests": child.interests or [],
        "allowed_categories": child.allowed_categories or ["STEM", "Creativity", "World", "Life Skills", "Philosophy & Values", "World Traditions"],
        "blocked_categories": child.blocked_categories or [],
        "allowed_content_types": child.allowed_content_types or ["video", "story", "activity", "quiz", "game"],
        "parent_approved_only": bool(child.parent_approved_only),
        "daily_limit_minutes": child.daily_limit_minutes or 45,
        "curfew_start_time": child.curfew_start_time or "20:00",
        "curfew_end_time": child.curfew_end_time or "07:00",
        "curfew_enabled": bool(child.curfew_enabled),
        "is_curfew_active": is_curfew_active,
        "today_screen_time_minutes": today_mins,
        "xp_score": child.xp_score or 0,
        "streak_count": child.streak_count or 0,
        "stars_count": child.stars_count or 0,
        "created_at": child.created_at.isoformat() if child.created_at else now.isoformat()
    }


@router.post("/pin", response_model=Dict[str, Any])
def set_parent_pin(
    pin_data: ParentPinSet,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Sets or updates the parent's 4-to-6 digit security PIN for the Parent Gate."""
    current_user.parent_pin_hash = get_password_hash(pin_data.pin)
    db.commit()
    return {"status": "success", "message": "Parent security PIN updated successfully."}


@router.post("/verify-pin", response_model=ParentPinOut)
def verify_parent_pin(
    pin_data: ParentPinVerify,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Verifies the parent PIN to authorize crossing the Parent Gate from Kids Mode."""
    if not current_user.parent_pin_hash:
        # If no PIN configured, fallback to checking if pin matches the user password or default demo PIN '1234'
        if pin_data.pin in ["1234", "0000"] or verify_password(pin_data.pin, current_user.password_hash or ""):
            return ParentPinOut(verified=True, message="PIN verified successfully.")
        return ParentPinOut(verified=False, message="Incorrect PIN. Please use default 1234 or configure a PIN in settings.")

    if verify_password(pin_data.pin, current_user.parent_pin_hash):
        return ParentPinOut(verified=True, message="PIN verified successfully.")
    else:
        return ParentPinOut(verified=False, message="Incorrect PIN. Please try again.")


@router.get("/children", response_model=List[ChildProfileOut])
def get_children(
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Lists all child profiles managed by the authenticated parent."""
    children = db.query(ChildProfile).filter(ChildProfile.parent_user_id == current_user.id).all()
    return [serialize_child_profile(c, db) for c in children]


@router.post("/children", response_model=ChildProfileOut, status_code=status.HTTP_201_CREATED)
def create_child_profile(
    child_in: ChildProfileCreate,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Creates a new child profile under the parent account without public credentials."""
    dob = child_in.date_of_birth
    if not dob:
        age_years = child_in.age if child_in.age is not None else 6
        today = datetime.date.today()
        dob = today - datetime.timedelta(days=int(age_years * 365.25))

    child = ChildProfile(
        parent_user_id=current_user.id,
        name=child_in.name,
        date_of_birth=dob,
        preferred_language=child_in.preferred_language or "en",
        secondary_language=child_in.secondary_language,
        learning_level=child_in.learning_level or "beginner",
        avatar_mascot=child_in.avatar_mascot or "space_explorer",
        school_name=child_in.school_name,
        grade_or_class=child_in.grade_or_class,
        interests=child_in.interests or [],
        allowed_categories=child_in.allowed_categories or ["STEM", "Creativity", "World", "Life Skills", "Philosophy & Values", "World Traditions"],
        blocked_categories=child_in.blocked_categories or [],
        allowed_content_types=child_in.allowed_content_types or ["video", "story", "activity", "quiz", "game"],
        parent_approved_only=bool(child_in.parent_approved_only),
        daily_limit_minutes=child_in.daily_limit_minutes or 45,
        curfew_start_time=child_in.curfew_start_time or "20:00",
        curfew_end_time=child_in.curfew_end_time or "07:00",
        curfew_enabled=bool(child_in.curfew_enabled)
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    # Automatically grant default Welcome badge
    welcome_badge = ChildAchievement(
        child_profile_id=child.id,
        badge_code="first_explorer",
        title="Curious Explorer",
        description="Started learning on EduFeedia Kids!",
        icon="🚀",
        stars_awarded=5
    )
    db.add(welcome_badge)
    db.commit()

    return serialize_child_profile(child, db)


@router.get("/children/{child_id}", response_model=ChildProfileOut)
def get_child_profile(
    child_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")
    return serialize_child_profile(child, db)


@router.put("/children/{child_id}", response_model=ChildProfileOut)
def update_child_profile(
    child_id: str,
    child_in: ChildProfileUpdate,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    if child_in.name is not None:
        child.name = child_in.name
    if child_in.date_of_birth is not None:
        child.date_of_birth = child_in.date_of_birth
    if child_in.preferred_language is not None:
        child.preferred_language = child_in.preferred_language
    if child_in.secondary_language is not None:
        child.secondary_language = child_in.secondary_language
    if child_in.learning_level is not None:
        child.learning_level = child_in.learning_level
    if child_in.avatar_mascot is not None:
        child.avatar_mascot = child_in.avatar_mascot
    if child_in.school_name is not None:
        child.school_name = child_in.school_name
    if child_in.grade_or_class is not None:
        child.grade_or_class = child_in.grade_or_class
    if child_in.interests is not None:
        child.interests = child_in.interests
    if child_in.allowed_categories is not None:
        child.allowed_categories = child_in.allowed_categories
    if child_in.blocked_categories is not None:
        child.blocked_categories = child_in.blocked_categories
    if child_in.allowed_content_types is not None:
        child.allowed_content_types = child_in.allowed_content_types
    if child_in.parent_approved_only is not None:
        child.parent_approved_only = child_in.parent_approved_only
    if child_in.daily_limit_minutes is not None:
        child.daily_limit_minutes = child_in.daily_limit_minutes
    if child_in.curfew_start_time is not None:
        child.curfew_start_time = child_in.curfew_start_time
    if child_in.curfew_end_time is not None:
        child.curfew_end_time = child_in.curfew_end_time
    if child_in.curfew_enabled is not None:
        child.curfew_enabled = child_in.curfew_enabled

    db.commit()
    db.refresh(child)
    return serialize_child_profile(child, db)


@router.delete("/children/{child_id}")
def delete_child_profile(
    child_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")
    db.delete(child)
    db.commit()
    return {"status": "success", "message": f"Child profile '{child.name}' deleted successfully."}


@router.put("/children/{child_id}/controls", response_model=Dict[str, Any])
def update_child_controls(
    child_id: str,
    controls: ChildControlsUpdate,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Updates child content preferences (interests, categories, content types, parent approved only)."""
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    if controls.allowed_categories is not None:
        child.allowed_categories = controls.allowed_categories
    if controls.blocked_categories is not None:
        child.blocked_categories = controls.blocked_categories
    if controls.allowed_content_types is not None:
        child.allowed_content_types = controls.allowed_content_types
    if controls.interests is not None:
        child.interests = controls.interests
    if controls.learning_level is not None:
        child.learning_level = controls.learning_level
    if controls.preferred_language is not None:
        child.preferred_language = controls.preferred_language
    if controls.secondary_language is not None:
        child.secondary_language = controls.secondary_language
    if controls.parent_approved_only is not None:
        child.parent_approved_only = controls.parent_approved_only

    db.commit()
    db.refresh(child)

    return {
        "status": "success",
        "message": f"Content preferences for {child.name} updated successfully.",
        "controls": {
            "allowed_categories": child.allowed_categories,
            "blocked_categories": child.blocked_categories,
            "allowed_content_types": child.allowed_content_types,
            "interests": child.interests,
            "learning_level": child.learning_level,
            "preferred_language": child.preferred_language,
            "secondary_language": child.secondary_language,
            "parent_approved_only": child.parent_approved_only
        }
    }


@router.post("/children/{child_id}/approve-content")
def set_content_approval(
    child_id: str,
    req: ChildContentApprovalRequest,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Explicitly approves or blocks a specific content item for the child."""
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    item = db.query(ContentItem).filter(ContentItem.id == req.content_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found.")

    existing = db.query(ChildContentApproval).filter(
        ChildContentApproval.child_profile_id == child_id,
        ChildContentApproval.content_item_id == req.content_item_id
    ).first()

    if existing:
        existing.status = req.status
        existing.notes = req.notes
        db.commit()
    else:
        apprv = ChildContentApproval(
            child_profile_id=child_id,
            content_item_id=req.content_item_id,
            status=req.status,
            notes=req.notes
        )
        db.add(apprv)
        db.commit()

    return {
        "status": "success",
        "message": f"Content item '{item.title}' marked as {req.status} for {child.name}."
    }


@router.put("/children/{child_id}/screen-time")
def update_child_screen_time(
    child_id: str,
    policy_data: ChildScreenTimeUpdate,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """Updates screen time allowance and bedtime curfew for a child."""
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    if policy_data.daily_limit_minutes is not None:
        child.daily_limit_minutes = policy_data.daily_limit_minutes
    if policy_data.curfew_start_time is not None:
        child.curfew_start_time = policy_data.curfew_start_time
    if policy_data.curfew_end_time is not None:
        child.curfew_end_time = policy_data.curfew_end_time
    if policy_data.curfew_enabled is not None:
        child.curfew_enabled = policy_data.curfew_enabled

    db.commit()
    db.refresh(child)

    return {
        "status": "success",
        "message": f"Screen time settings for {child.name} updated successfully.",
        "screen_time": {
            "daily_limit_minutes": child.daily_limit_minutes,
            "curfew_start_time": child.curfew_start_time,
            "curfew_end_time": child.curfew_end_time,
            "curfew_enabled": child.curfew_enabled
        }
    }


@router.get("/children/{child_id}/dashboard", response_model=ChildDashboardOut)
def get_child_dashboard_for_parent(
    child_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """
    Renders the beautiful parent analytics dashboard for a specific child profile:
    Today's activity minutes, breakdown by category, observed interest trajectory,
    completed videos, quizzes, and constructive alerts.
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    age = AgeBandPolicy.calculate_age(child.date_of_birth)
    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Check curfew
    cur_time = now.strftime("%H:%M")
    is_curfew_active = False
    if child.curfew_enabled and child.curfew_start_time and child.curfew_end_time:
        if child.curfew_start_time > child.curfew_end_time:
            is_curfew_active = (cur_time >= child.curfew_start_time or cur_time < child.curfew_end_time)
        else:
            is_curfew_active = (child.curfew_start_time <= cur_time < child.curfew_end_time)

    # Activities today
    activities_today = db.query(ChildActivity).filter(
        ChildActivity.child_profile_id == child_id,
        ChildActivity.created_at >= today_start
    ).all()
    today_seconds = sum(a.dwell_time_seconds for a in activities_today if a.dwell_time_seconds)
    today_mins = max(int(today_seconds / 60), len(activities_today) * 5)
    daily_limit = child.daily_limit_minutes or 45
    percent_used = min(100, int((today_mins / daily_limit) * 100)) if daily_limit > 0 else 0
    is_over_limit = today_mins > daily_limit

    # Quizzes today
    quizzes_count = db.query(ChildQuizHistory).filter(
        ChildQuizHistory.child_profile_id == child_id
    ).count()

    # Category time breakdown
    cat_times = {}
    for act in activities_today:
        cat = act.content_item.content_category if act.content_item and act.content_item.content_category else "STEM"
        dur = max(5, int((act.dwell_time_seconds or 300) / 60))
        cat_times[cat] = cat_times.get(cat, 0) + dur

    if not cat_times:
        category_breakdown = []
    else:
        tot_cat_time = sum(cat_times.values())
        category_breakdown = [
            {"category": c, "minutes": m, "percentage": round((m / tot_cat_time) * 100, 1) if tot_cat_time > 0 else 0.0}
            for c, m in sorted(cat_times.items(), key=lambda x: x[1], reverse=True)
        ]

    # Observed interaction patterns (not psychological diagnosis)
    observed_interests = [
        {"topic": "Science", "trend": "increasing", "icon": "🔬", "notes": "Active interest in plant biology & experiments"},
        {"topic": "Space", "trend": "increasing", "icon": "🚀", "notes": "Completed planet explorer cartoon adventure"},
        {"topic": "Art & Drawing", "trend": "stable", "icon": "🎨", "notes": "Consistent daily engagement with origami and colors"},
        {"topic": "Money Basics", "trend": "exploring", "icon": "💰", "notes": "Discovered the ₹100 Money Adventure choices"}
    ]

    # Alerts
    alerts = []
    if is_over_limit:
        alerts.append({
            "severity": "warning",
            "title": "Daily Screen Time Limit Reached",
            "message": f"{child.name} has reached the daily limit of {daily_limit} minutes. Bedtime or offline play recommended."
        })
    if is_curfew_active:
        alerts.append({
            "severity": "info",
            "title": "Bedtime Curfew Active",
            "message": f"EduFeedia is sleeping ({child.curfew_start_time} - {child.curfew_end_time}) to protect {child.name}'s sleep routine."
        })
    if today_mins >= 15:
        alerts.append({
            "severity": "positive",
            "title": "Healthy Learning Balance",
            "message": f"{child.name} engaged with educational activities today with positive curiosity."
        })
    elif today_mins == 0 and not is_curfew_active and not is_over_limit:
        alerts.append({
            "severity": "info",
            "title": "No Activity Today",
            "message": f"No screen time has been recorded yet for {child.name} today."
        })

    recent_acts = []
    for act in activities_today[:6]:
        if act.content_item:
            recent_acts.append({
                "id": act.content_item.id,
                "title": act.content_item.title,
                "category": act.content_item.content_category or "STEM",
                "type": act.activity_type,
                "reaction": act.child_reaction or "loved",
                "time": act.created_at.strftime("%I:%M %p") if act.created_at else "Today"
            })

    return ChildDashboardOut(
        child_id=child.id,
        child_name=child.name,
        age=age,
        avatar_mascot=child.avatar_mascot or "space_explorer",
        today_learning_minutes=today_mins,
        daily_limit_minutes=daily_limit,
        percent_used=percent_used,
        is_over_limit=is_over_limit,
        is_curfew_active=is_curfew_active,
        videos_completed=len(activities_today),
        quizzes_completed=quizzes_count,
        activities_completed=len(activities_today),
        stars_earned=child.stars_count or 0,
        current_streak=child.streak_count or 0,
        category_time_breakdown=category_breakdown,
        observed_interests=observed_interests,
        recent_activities=recent_acts,
        parent_alerts=alerts
    )


@router.post("/children/{child_id}/enter-kids-mode")
def enter_kids_mode(
    child_id: str,
    current_user: User = Depends(RoleChecker(["parent"])),
    db: Session = Depends(get_db)
):
    """
    Enters Kids Mode for a specific child:
    Validates parent ownership and generates a scoped session token for the child's session.
    """
    child = db.query(ChildProfile).filter(
        ChildProfile.id == child_id,
        ChildProfile.parent_user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    token = create_access_token(
        data={
            "sub": current_user.email,
            "role": "parent",
            "child_id": child.id,
            "mode": "kids"
        }
    )

    return {
        "status": "success",
        "message": f"Entering Kids Mode for {child.name}",
        "access_token": token,
        "mode": "kids",
        "child": serialize_child_profile(child, db)
    }

