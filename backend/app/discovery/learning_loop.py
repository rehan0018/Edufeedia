"""
Closed Learning Loop Manager.
Connects search discovery -> resource engagement -> concept-check quiz -> mastery index update -> personalized reranking.
Turns Edufeedia from a static content index into an adaptive learning operating system.
"""

import time
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    User, StudentProfile, TopicMastery, StudentMasteryHistory,
    LearningEvent, RewardLedger
)
from app.schemas.schemas import (
    QuizSubmitRequest, QuizSubmitResponse, ResourceEngagementRequest,
    InterpretedIntent
)
from app.discovery.pipeline import DiscoveryPipeline


class LearningLoopManager:
    """
    Manages student mastery progression, quiz evaluation, and reinforcement pathways.
    """

    @classmethod
    def evaluate_quiz_submission(
        cls,
        db: Session,
        student_user: Optional[User],
        request: QuizSubmitRequest
    ) -> QuizSubmitResponse:
        """
        Grades a submitted concept-check quiz, calculates mastery deltas,
        updates the student's mastery record, and logs audit history.
        """
        # 1. Retrieve the ground-truth quiz questions
        synthetic_intent = InterpretedIntent(
            subject=request.subject or "Science",
            topic=request.topic,
            grade_level=request.grade_level,
            board="CBSE",
            intent_type="explanation",
            depth_level="standard",
            format_preference="all",
            language="en",
            expanded_terms=[]
        )
        quiz_data = DiscoveryPipeline.generate_concept_check(synthetic_intent)
        question_map = {q.id: q for q in quiz_data.questions}

        # 2. Grade each submitted answer
        correct_count = 0
        total_questions = len(quiz_data.questions)
        question_results: List[Dict[str, Any]] = []

        for q in quiz_data.questions:
            student_chosen = request.answers.get(q.id)
            is_correct = (student_chosen is not None and student_chosen == q.correct_option_index)
            if is_correct:
                correct_count += 1

            chosen_text = None
            if student_chosen is not None and 0 <= student_chosen < len(q.options):
                chosen_text = q.options[student_chosen]

            question_results.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "selected_option_index": student_chosen,
                "selected_option_text": chosen_text,
                "correct_option_index": q.correct_option_index,
                "correct_option_text": q.options[q.correct_option_index],
                "is_correct": is_correct,
                "explanation": q.explanation
            })

        accuracy_pct = round((correct_count / max(1, total_questions)) * 100.0, 1)

        # 3. Retrieve or initialize student's topic mastery
        student_id = student_user.id if student_user else "anonymous-student"
        prior_mastery = 40.0

        topic_record = None
        if student_user:
            topic_record = db.query(TopicMastery).filter(
                TopicMastery.student_user_id == student_id,
                TopicMastery.subject.ilike(f"%{request.subject}%"),
                TopicMastery.topic.ilike(f"%{request.topic}%")
            ).first()

            if not topic_record:
                # Fallback to topic search across subjects
                topic_record = db.query(TopicMastery).filter(
                    TopicMastery.student_user_id == student_id,
                    TopicMastery.topic.ilike(f"%{request.topic}%")
                ).first()

            if topic_record:
                prior_mastery = float(topic_record.mastery_score or 0.0)

        # 4. Calculate adaptive mastery delta (Bayesian Knowledge Tracing inspired)
        # High score: large gain. Low score: minor adjustment to protect motivation while identifying weakness.
        if accuracy_pct >= 80.0:
            mastery_gain = round(15.0 + (accuracy_pct - 80.0) * 0.25, 2)
            trend = "improving"
        elif accuracy_pct >= 60.0:
            mastery_gain = round(5.0 + (accuracy_pct - 60.0) * 0.25, 2)
            trend = "improving"
        elif accuracy_pct >= 40.0:
            mastery_gain = -2.5
            trend = "stable"
        else:
            mastery_gain = -6.0
            trend = "declining"

        new_mastery = round(max(5.0, min(100.0, prior_mastery + mastery_gain)), 1)
        actual_gain = round(new_mastery - prior_mastery, 1)

        # 5. Persist TopicMastery and StudentMasteryHistory in database
        xp_earned = int(40 + (correct_count * 12) + (20 if accuracy_pct >= 80 else 0))

        if student_user:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            if topic_record:
                topic_record.mastery_score = new_mastery
                topic_record.attempt_count = (topic_record.attempt_count or 0) + 1
                topic_record.trend = trend
                topic_record.last_assessed_at = now_utc
            else:
                topic_record = TopicMastery(
                    student_user_id=student_id,
                    board="CBSE",
                    grade_level=request.grade_level,
                    subject=request.subject or "Science",
                    topic=request.topic,
                    mastery_score=new_mastery,
                    confidence=0.75 if accuracy_pct >= 60 else 0.45,
                    attempt_count=1,
                    trend=trend,
                    last_assessed_at=now_utc
                )
                db.add(topic_record)

            # Record mastery history row
            history_entry = StudentMasteryHistory(
                student_user_id=student_id,
                topic=request.topic,
                subject=request.subject or "Science",
                prior_mastery=prior_mastery,
                new_mastery=new_mastery,
                learning_gain=actual_gain,
                quiz_score_pct=accuracy_pct
            )
            db.add(history_entry)

            # Log learning event
            event = LearningEvent(
                student_user_id=student_id,
                event_type="quiz_submission",
                progress_percentage=int(accuracy_pct),
                verified_seconds=90,
                heartbeat_count=3,
                client_timestamp=now_utc
            )
            db.add(event)

            # Credit reward ledger idempotently
            unique_key = f"xp:discovery_quiz:{student_id}:{request.quiz_id}:{int(time.time() // 60)}"
            ledger_entry = RewardLedger(
                student_user_id=student_id,
                reward_type="QUIZ_MASTERY_XP",
                xp_amount=xp_earned,
                unique_reward_key=unique_key
            )
            db.add(ledger_entry)

            # Update student profile XP if present
            profile = getattr(student_user, "student_profile", None)
            if profile:
                profile.xp_score = (profile.xp_score or 0) + xp_earned

            db.commit()

        # 6. Socratic Feedback and Recommended Next Step
        if accuracy_pct >= 80.0:
            feedback = f"Outstanding work! You scored {correct_count}/{total_questions} ({accuracy_pct}%). You demonstrate thorough conceptual mastery of {request.topic}."
            recommended_next_step = "Proceed to the 'Go Deeper' section to explore higher-order principles and advanced simulations."
        elif accuracy_pct >= 60.0:
            feedback = f"Good job! You scored {correct_count}/{total_questions} ({accuracy_pct}%). Your core intuition is sound, with a few nuances to reinforce."
            recommended_next_step = "Review the NCERT reading excerpts or test your hypothesis with the interactive PhET simulation."
        else:
            feedback = f"You answered {correct_count}/{total_questions} correctly ({accuracy_pct}%). Do not worry—learning is iterative."
            recommended_next_step = f"We have recalibrated your recommendations. Watch the visual Socratic animation again and review prerequisite fundamentals."

        return QuizSubmitResponse(
            quiz_id=request.quiz_id,
            score=correct_count,
            total_questions=total_questions,
            accuracy_percentage=accuracy_pct,
            prior_mastery=prior_mastery,
            new_mastery=new_mastery,
            mastery_gain=actual_gain,
            xp_earned=xp_earned,
            feedback=feedback,
            question_results=question_results,
            recommended_next_step=recommended_next_step
        )

    @classmethod
    def record_resource_engagement(
        cls,
        db: Session,
        student_user: Optional[User],
        request: ResourceEngagementRequest
    ) -> Dict[str, Any]:
        """
        Records student engagement with a discovered resource (dwell time, completion).
        """
        student_id = student_user.id if student_user else "anonymous-student"
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        if student_user:
            event = LearningEvent(
                student_user_id=student_id,
                content_item_id=None,
                event_type="progress_checkpoint" if request.action_type == "viewed" else "completion_verified",
                progress_percentage=100 if request.action_type == "completed" else min(90, int(request.dwell_time_seconds / 3)),
                verified_seconds=request.dwell_time_seconds,
                heartbeat_count=max(1, request.dwell_time_seconds // 30),
                client_timestamp=now_utc
            )
            db.add(event)

            # If student completed a resource or spent > 3 minutes, provide an engagement XP reward
            xp_bonus = 0
            if request.action_type == "completed" or request.dwell_time_seconds >= 180:
                xp_bonus = 20
                unique_key = f"xp:resource_engagement:{student_id}:{request.resource_id}:{int(time.time() // 300)}"
                ledger = RewardLedger(
                    student_user_id=student_id,
                    reward_type="CONTENT_COMPLETION_XP",
                    xp_amount=xp_bonus,
                    unique_reward_key=unique_key
                )
                db.add(ledger)
                profile = getattr(student_user, "student_profile", None)
                if profile:
                    profile.xp_score = (profile.xp_score or 0) + xp_bonus

            db.commit()

        return {
            "status": "recorded",
            "resource_id": request.resource_id,
            "topic": request.topic,
            "dwell_time_seconds": request.dwell_time_seconds,
            "action_type": request.action_type,
            "xp_awarded": 20 if (request.action_type == "completed" or request.dwell_time_seconds >= 180) else 0
        }
