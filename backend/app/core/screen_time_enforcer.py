"""
Authoritative Server-Side Screen Time and Curfew Policy Enforcer.
Provides centralized policy evaluation, telemetry session calculation, and request gating.
Enforces daily screen time bounds, bedtime curfew, and AI tutor quotas across all student touchpoints.
"""

import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    User, ParentalScreenTimePolicy, LearningEvent, UserInteraction, QuizAttempt
)
from app.core.security import get_current_user


class ScreenTimePolicyEnforcer:
    """
    Enforces parental screen-time quotas, bedtime curfews, and Socratic AI limits.
    Prevents client-side bypasses by gating server-side learning endpoints.
    """

    @staticmethod
    def get_or_create_policy(db: Session, student_id: str) -> ParentalScreenTimePolicy:
        """Retrieves or provides a default parental screen-time policy for a student."""
        policy = db.query(ParentalScreenTimePolicy).filter(
            ParentalScreenTimePolicy.student_user_id == student_id
        ).first()

        if not policy:
            policy = ParentalScreenTimePolicy(
                parent_user_id=student_id,  # System default assignment if parent not linked
                student_user_id=student_id,
                daily_limit_minutes=90,
                curfew_start_time="21:30",
                curfew_end_time="06:30",
                curfew_enabled=True,
                ai_tutor_max_daily_minutes=30,
                break_interval_minutes=45
            )
            try:
                db.add(policy)
                db.commit()
                db.refresh(policy)
            except Exception:
                db.rollback()
                policy = db.query(ParentalScreenTimePolicy).filter(
                    ParentalScreenTimePolicy.student_user_id == student_id
                ).first() or policy

        return policy

    @classmethod
    def get_screen_time_status(cls, db: Session, student_id: str) -> Dict[str, Any]:
        """
        Calculates verified real screen time, AI tutor usage, and curfew status
        strictly derived from authoritative telemetry logs (LearningEvent + UserInteraction).
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        policy = cls.get_or_create_policy(db, student_id)

        # 1. Authoritative telemetry: verified seconds from LearningEvent logs
        events_today = db.query(LearningEvent).filter(
            LearningEvent.student_user_id == student_id,
            LearningEvent.created_at >= today_start
        ).all()
        learning_seconds = sum(e.verified_seconds for e in events_today if e.verified_seconds)

        # 2. Dwell-time from user interactions
        interactions_today = db.query(UserInteraction).filter(
            UserInteraction.user_id == student_id,
            UserInteraction.created_at >= today_start
        ).all()
        interaction_seconds = sum(i.dwell_time_seconds for i in interactions_today if i.dwell_time_seconds)

        # 3. Quizzes completed today
        quizzes_today = db.query(QuizAttempt).filter(
            QuizAttempt.student_user_id == student_id,
            QuizAttempt.completed_at >= today_start
        ).count()

        # Telemetry is strictly measured, avoiding arbitrary floor injections
        total_seconds = max(learning_seconds, interaction_seconds) + (quizzes_today * 300)
        today_minutes = int(total_seconds / 60)

        # 4. Measure AI tutor queries today
        ai_queries_today = db.query(UserInteraction).filter(
            UserInteraction.user_id == student_id,
            UserInteraction.interaction_type == "ai_query",
            UserInteraction.created_at >= today_start
        ).count()
        ai_minutes = ai_queries_today * 3

        # 5. Curfew calculation (supports cross-midnight curfew: 21:30 -> 06:30)
        current_time_str = now.strftime("%H:%M")
        is_curfew_active = False
        if policy.curfew_enabled and policy.curfew_start_time and policy.curfew_end_time:
            c_start = policy.curfew_start_time
            c_end = policy.curfew_end_time
            if c_start > c_end:
                # e.g. 21:30 to 06:30
                is_curfew_active = (current_time_str >= c_start or current_time_str < c_end)
            else:
                is_curfew_active = (c_start <= current_time_str < c_end)

        daily_limit = policy.daily_limit_minutes or 90
        ai_limit = policy.ai_tutor_max_daily_minutes or 30
        is_over_limit = today_minutes >= daily_limit
        is_ai_tutor_locked = ai_minutes >= ai_limit

        is_locked = is_curfew_active or is_over_limit

        lock_reason = None
        lock_message = ""
        if is_curfew_active:
            lock_reason = "curfew"
            lock_message = (
                f"Bedtime curfew active: Study sessions are locked between {policy.curfew_start_time} "
                f"and {policy.curfew_end_time} to support healthy sleep hygiene."
            )
        elif is_over_limit:
            lock_reason = "daily_limit"
            lock_message = (
                f"Daily screen time limit reached: You have consumed {today_minutes}m of your "
                f"allocated {daily_limit}m daily learning time. Time for a screen-free break!"
            )

        return {
            "student_id": student_id,
            "today_minutes": today_minutes,
            "daily_limit_minutes": daily_limit,
            "remaining_minutes": max(0, daily_limit - today_minutes),
            "is_over_limit": is_over_limit,
            "curfew_enabled": policy.curfew_enabled,
            "curfew_start_time": policy.curfew_start_time,
            "curfew_end_time": policy.curfew_end_time,
            "is_curfew_active": is_curfew_active,
            "is_locked": is_locked,
            "lock_reason": lock_reason,
            "lock_message": lock_message,
            "ai_tutor_minutes": ai_minutes,
            "ai_tutor_max_daily_minutes": ai_limit,
            "is_ai_tutor_locked": is_ai_tutor_locked,
            "ai_tutor_remaining_minutes": max(0, ai_limit - ai_minutes)
        }

    @classmethod
    def check_access(
        cls,
        db: Session,
        user: User,
        action: str = "general"
    ) -> Dict[str, Any]:
        """
        Enforces parental policies on student actions.
        Raises HTTP 423 (Locked) if curfew or screen-time bounds are exceeded.
        """
        # Only students are constrained by child screen time policies
        if user.role != "student":
            return {"allowed": True}

        status_info = cls.get_screen_time_status(db, user.id)

        # 1. Enforce Bedtime Curfew
        if status_info["is_curfew_active"]:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=status_info["lock_message"] or "Bedtime curfew active: Study sessions are locked."
            )

        # 2. Enforce Daily Screen Time Limit
        if status_info["is_over_limit"]:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=status_info["lock_message"] or "Daily screen time limit reached."
            )

        # 3. Enforce AI Tutor Quota
        if action == "ai_tutor" and status_info["is_ai_tutor_locked"]:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=(
                    f"Daily Socratic AI tutoring limit reached ({status_info['ai_tutor_minutes']}m / "
                    f"{status_info['ai_tutor_max_daily_minutes']}m). Continue learning with curriculum lessons and quizzes."
                )
            )

        return status_info


def verify_student_screen_time(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Dependency for gating general student endpoints (curriculum, feed, activities)."""
    ScreenTimePolicyEnforcer.check_access(db, current_user, action="general")
    return current_user


def verify_student_ai_tutor_quota(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Dependency for gating AI tutor access specifically."""
    ScreenTimePolicyEnforcer.check_access(db, current_user, action="ai_tutor")
    return current_user
