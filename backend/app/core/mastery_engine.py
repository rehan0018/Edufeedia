import datetime
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import (
    TopicMastery, QuizAttempt, Quiz, Question, SpacedRepetitionSchedule,
    StudentProfile, Badge, UserBadge, User
)

logger = logging.getLogger(__name__)

class MasteryEngine:
    """
    Closed-Loop Diagnostic Learning Intelligence & Topic Mastery Engine.
    1. Server-Side Quiz Grading & Accuracy Calculation
    2. Exponential Moving Average Topic Mastery (M_t = 0.70 * M_{t-1} + 0.30 * Score)
    3. Performance Trajectory Trend Analysis ('improving', 'stable', 'declining')
    4. SM-2 Spaced Repetition Integration
    5. Event-Driven Gamification & Badge Dispatch
    """

    @classmethod
    def evaluate_quiz_submission(
        cls,
        db: Session,
        student_id: str,
        quiz_id: str,
        user_answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found.")

        questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        if not questions:
            raise ValueError("No questions associated with this quiz.")

        total_questions = len(questions)
        correct_count = 0
        detailed_breakdown = []

        # Server-side answer verification
        for q in questions:
            submitted = user_answers.get(str(q.id)) or user_answers.get(q.id)
            is_correct = False
            if submitted is not None:
                if isinstance(submitted, int) and q.options and 0 <= submitted < len(q.options):
                    is_correct = (str(q.options[submitted]).strip().lower() == str(q.correct_answer or '').strip().lower())
                else:
                    is_correct = (str(submitted).strip().lower() == str(q.correct_answer or '').strip().lower())

            if is_correct:
                correct_count += 1

            detailed_breakdown.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "submitted_answer": submitted,
                "is_correct": is_correct,
                "explanation": q.explanation or "Curriculum principle reviewed."
            })

        max_score = total_questions * 10
        earned_score = correct_count * 10
        accuracy = round((correct_count / max(1, total_questions)) * 100.0, 1)

        # Existing attempt count
        prev_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_user_id == student_id,
            QuizAttempt.quiz_id == quiz_id
        ).count()
        attempt_number = prev_attempts + 1

        # Calculate XP: 50 base XP + 5 XP per correct question + 25 bonus for mastery (>=80%)
        xp_earned = 50 + (correct_count * 5) + (25 if accuracy >= 80.0 else 0)

        # 1. Record QuizAttempt
        attempt = QuizAttempt(
            student_user_id=student_id,
            quiz_id=quiz_id,
            score=earned_score,
            max_score=max_score,
            accuracy_percentage=Decimal(str(accuracy)),
            attempt_number=attempt_number,
            xp_awarded=xp_earned,
            completed_at=datetime.datetime.utcnow()
        )
        db.add(attempt)

        # 2. Update Student Profile XP & Streaks
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        if profile:
            profile.xp_score = (profile.xp_score or 0) + xp_earned
            today = datetime.date.today()
            if profile.last_active_date:
                diff = (today - profile.last_active_date).days
                if diff == 1:
                    profile.streak_count = (profile.streak_count or 0) + 1
                elif diff > 1:
                    profile.streak_count = 1
            else:
                profile.streak_count = 1
        # 3. Update or Create TopicMastery Record
        subject = (quiz.content_item.subject if quiz.content_item else getattr(quiz, "subject", None)) or "Science"
        topic = (quiz.content_item.topic if quiz.content_item else getattr(quiz, "topic", None)) or "Physics"
        board = (quiz.content_item.board if quiz.content_item else getattr(quiz, "board", None)) or "CBSE"
        grade_level = (quiz.content_item.grade_level if quiz.content_item else getattr(quiz, "grade_level", None)) or 10
        mastery_info = cls.update_topic_mastery(
            db=db,
            student_id=student_id,
            subject=subject,
            topic=topic,
            quiz_score_pct=accuracy,
            board=board,
            grade_level=grade_level
        )

        # 4. Integrate SM-2 Spaced Repetition Schedule
        sm2_info = cls.update_spaced_repetition(
            db=db,
            student_id=student_id,
            subject=subject,
            topic=topic,
            accuracy_pct=accuracy
        )

        # 5. Process Learning Events & Badges
        unlocked_badges = cls._process_learning_events(
            db=db,
            student_id=student_id,
            accuracy=accuracy,
            profile=profile
        )

        db.commit()

        return {
            "attempt_id": attempt.id,
            "quiz_id": quiz_id,
            "score": earned_score,
            "max_score": max_score,
            "accuracy_percentage": accuracy,
            "xp_awarded": xp_earned,
            "topic_mastery": mastery_info,
            "spaced_repetition": sm2_info,
            "unlocked_badges": unlocked_badges,
            "breakdown": detailed_breakdown
        }

    @classmethod
    def update_topic_mastery(
        cls,
        db: Session,
        student_id: str,
        subject: str,
        topic: str,
        quiz_score_pct: float,
        board: str = "CBSE",
        grade_level: int = 10
    ) -> Dict[str, Any]:
        mastery_record = db.query(TopicMastery).filter(
            TopicMastery.student_user_id == student_id,
            TopicMastery.subject == subject,
            TopicMastery.topic == topic
        ).first()

        new_score_dec = Decimal(str(round(quiz_score_pct, 2)))

        if not mastery_record:
            mastery_record = TopicMastery(
                student_user_id=student_id,
                board=board,
                grade_level=grade_level,
                subject=subject,
                topic=topic,
                mastery_score=new_score_dec,
                confidence=Decimal("0.60"),
                attempt_count=1,
                trend="stable",
                last_assessed_at=datetime.datetime.utcnow()
            )
            db.add(mastery_record)
        else:
            old_score = float(mastery_record.mastery_score or 0.0)
            # Exponential Moving Average: 70% prior mastery weight + 30% new performance
            updated_score = (0.70 * old_score) + (0.30 * quiz_score_pct)
            
            # Trend calculation
            if updated_score >= old_score + 5.0:
                trend = "improving"
            elif updated_score <= old_score - 5.0:
                trend = "declining"
            else:
                trend = "stable"

            mastery_record.mastery_score = Decimal(str(round(updated_score, 2)))
            mastery_record.attempt_count = (mastery_record.attempt_count or 0) + 1
            mastery_record.confidence = min(Decimal("0.98"), Decimal(str(round(float(mastery_record.confidence or 0.5) + 0.10, 2))))
            mastery_record.trend = trend
            mastery_record.last_assessed_at = datetime.datetime.utcnow()

        return {
            "subject": subject,
            "topic": topic,
            "mastery_score": float(mastery_record.mastery_score),
            "confidence": float(mastery_record.confidence),
            "attempt_count": mastery_record.attempt_count,
            "trend": mastery_record.trend
        }

    @classmethod
    def update_spaced_repetition(
        cls,
        db: Session,
        student_id: str,
        subject: str,
        topic: str,
        accuracy_pct: float
    ) -> Dict[str, Any]:
        schedule = db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student_id,
            SpacedRepetitionSchedule.subject == subject,
            SpacedRepetitionSchedule.topic == topic
        ).first()

        # Quality rating q in [0..5]
        q = min(5, max(0, int(round((accuracy_pct / 100.0) * 5))))

        if not schedule:
            schedule = SpacedRepetitionSchedule(
                student_user_id=student_id,
                subject=subject,
                topic=topic,
                interval_days=1 if q >= 3 else 1,
                repetition_number=1 if q >= 3 else 0,
                easiness_factor=Decimal("2.50"),
                next_review_date=datetime.date.today() + datetime.timedelta(days=1 if q >= 3 else 1)
            )
            db.add(schedule)
        else:
            rep = schedule.repetition_number or 0
            ef = float(schedule.easiness_factor or 2.50)
            
            # SM-2 Algorithm update
            if q >= 3:
                if rep == 0:
                    interval = 1
                elif rep == 1:
                    interval = 6
                else:
                    interval = int(round((schedule.interval_days or 1) * ef))
                rep += 1
            else:
                rep = 0
                interval = 1

            new_ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            new_ef = max(1.30, round(new_ef, 2))

            schedule.repetition_number = rep
            schedule.interval_days = interval
            schedule.easiness_factor = Decimal(str(new_ef))
            schedule.next_review_date = datetime.date.today() + datetime.timedelta(days=interval)

        return {
            "interval_days": schedule.interval_days,
            "repetition_number": schedule.repetition_number,
            "easiness_factor": float(schedule.easiness_factor),
            "next_review_date": str(schedule.next_review_date)
        }

    @classmethod
    def _process_learning_events(
        cls,
        db: Session,
        student_id: str,
        accuracy: float,
        profile: Optional[StudentProfile]
    ) -> List[str]:
        unlocked = []
        if accuracy >= 100.0:
            badge_name = "Perfectionist"
            b = db.query(Badge).filter(Badge.name == badge_name).first()
            if b:
                has_badge = db.query(UserBadge).filter(UserBadge.user_id == student_id, UserBadge.badge_id == b.id).first()
                if not has_badge:
                    db.add(UserBadge(user_id=student_id, badge_id=b.id))
                    unlocked.append(badge_name)

        if profile and (profile.streak_count or 0) >= 7:
            badge_name = "Week Streak"
            b = db.query(Badge).filter(Badge.name == badge_name).first()
            if b:
                has_badge = db.query(UserBadge).filter(UserBadge.user_id == student_id, UserBadge.badge_id == b.id).first()
                if not has_badge:
                    db.add(UserBadge(user_id=student_id, badge_id=b.id))
                    unlocked.append(badge_name)

        return unlocked
