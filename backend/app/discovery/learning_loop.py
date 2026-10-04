"""
Closed Learning Loop Manager.
Connects search discovery -> resource engagement -> concept-check quiz -> mastery index update -> personalized reranking.
Turns Edufeedia from a static content index into an adaptive learning operating system.
"""

import uuid
import time
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    User, StudentProfile, TopicMastery, StudentMasteryHistory,
    LearningEvent, RewardLedger, EmpiricalLearningGainRecord
)
from app.schemas.schemas import (
    QuizSubmitRequest, QuizSubmitResponse, ResourceEngagementRequest,
    InterpretedIntent, SessionStartRequest, SessionStartResponse,
    SessionHeartbeatRequest, SessionHeartbeatResponse, SessionEndRequest,
    SessionEndResponse, PrePostAssessmentSubmitRequest, EmpiricalLearningGainOut
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

        # 3. Retrieve student's topic mastery (requires authenticated student)
        if not student_user:
            raise ValueError("Student must be authenticated to submit concept-check quizzes and record mastery progression.")

        student_id = student_user.id
        prior_mastery = 40.0

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

        # 4. Calculate adaptive mastery delta (heuristic mastery update model; offline calibration required for validated BKT)
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

    # Server-authoritative session state registry:
    # Keyed by session_key: f"{student_id}:{session_id or resource_id}" -> {
    #     "started_at": datetime,
    #     "last_heartbeat_at": datetime,
    #     "accumulated_seconds": int,
    #     "heartbeat_count": int,
    #     "resource_id": str
    # }
    _ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def record_resource_engagement(
        cls,
        db: Session,
        student_user: Optional[User],
        request: ResourceEngagementRequest
    ) -> Dict[str, Any]:
        """
        Records student engagement with a discovered resource (dwell time, completion).
        Enforces session-isolated server-authoritative bounds:
        Dwell time is tracked per (student, resource, session) tuple so multiple concurrent
        tabs or different resources do not cross-pollinate or corrupt timestamps.
        Heartbeats are clamped to physical server elapsed time and anti-replay rate bounds.
        """
        if not student_user:
            raise ValueError("Student must be authenticated to record engagement telemetry.")

        student_id = student_user.id
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        session_key = f"{student_id}:{request.session_id or request.resource_id}"
        raw_dwell = max(0, int(request.dwell_time_seconds))

        if session_key in cls._ACTIVE_SESSIONS:
            sess = cls._ACTIVE_SESSIONS[session_key]
            last_created = sess["last_heartbeat_at"]
            if last_created.tzinfo is None:
                last_created = last_created.replace(tzinfo=datetime.timezone.utc)
            elapsed_server_seconds = max(0.0, (now_utc - last_created).total_seconds())

            # Anti-replay / rapid-fire attack check on this specific resource session:
            # If client sends another event within 2 seconds, physical elapsed time is negligible
            if elapsed_server_seconds < 2.0:
                verified_dwell = 0
            else:
                verified_dwell = min(raw_dwell, int(elapsed_server_seconds), 180)

            sess["last_heartbeat_at"] = now_utc
            sess["accumulated_seconds"] += verified_dwell
            sess["heartbeat_count"] += 1
            session_accumulated = sess["accumulated_seconds"]
            hb_count = sess["heartbeat_count"]
        else:
            # Initial heartbeat in this resource session
            verified_dwell = min(raw_dwell, 180)
            session_accumulated = verified_dwell
            hb_count = 1
            cls._ACTIVE_SESSIONS[session_key] = {
                "started_at": now_utc,
                "last_heartbeat_at": now_utc,
                "accumulated_seconds": session_accumulated,
                "heartbeat_count": hb_count,
                "resource_id": request.resource_id
            }

        event = LearningEvent(
            student_user_id=student_id,
            content_item_id=request.resource_id if len(request.resource_id) == 36 else None,
            event_type="progress_checkpoint" if request.action_type == "viewed" else "completion_verified",
            progress_percentage=100 if request.action_type == "completed" else min(90, int(session_accumulated / 2)),
            verified_seconds=verified_dwell,
            heartbeat_count=hb_count,
            client_timestamp=now_utc
        )
        db.add(event)

        # If student completed a resource or spent >= 180 seconds, provide an engagement XP reward
        xp_bonus = 0
        if request.action_type == "completed" or verified_dwell >= 180:
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
            "session_id": request.session_id or session_key,
            "resource_id": request.resource_id,
            "topic": request.topic,
            "dwell_time_seconds": verified_dwell,
            "session_accumulated_seconds": session_accumulated,
            "action_type": request.action_type,
            "xp_awarded": xp_bonus
        }

    @classmethod
    def start_learning_session(
        cls,
        student_user: Optional[User],
        request: SessionStartRequest
    ) -> SessionStartResponse:
        """
        Initializes an authoritative server-side learning session.
        Generates a unique session_id and registers server start time.
        """
        if not student_user:
            raise ValueError("Student must be authenticated to start a verified learning session.")

        student_id = student_user.id
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session_key = f"{student_id}:{session_id}"

        cls._ACTIVE_SESSIONS[session_key] = {
            "session_id": session_id,
            "student_id": student_id,
            "resource_id": request.resource_id,
            "topic": request.topic,
            "subject": request.subject,
            "grade_level": request.grade_level or 8,
            "started_at": now_utc,
            "last_heartbeat_at": now_utc,
            "accumulated_seconds": 0,
            "heartbeat_count": 0,
            "status": "active"
        }

        return SessionStartResponse(
            session_id=session_id,
            resource_id=request.resource_id,
            topic=request.topic,
            subject=request.subject,
            started_at=now_utc.isoformat(),
            status="active"
        )

    @classmethod
    def heartbeat_learning_session(
        cls,
        db: Session,
        student_user: Optional[User],
        request: SessionHeartbeatRequest
    ) -> SessionHeartbeatResponse:
        """
        Processes an authoritative incremental heartbeat for an active learning session.
        Clamps dwell time to physical elapsed wall-clock time and active visibility check.
        """
        if not student_user:
            raise ValueError("Student must be authenticated to pulse session heartbeats.")

        student_id = student_user.id
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        session_key = f"{student_id}:{request.session_id}"

        if session_key not in cls._ACTIVE_SESSIONS:
            cls._ACTIVE_SESSIONS[session_key] = {
                "session_id": request.session_id,
                "student_id": student_id,
                "resource_id": request.resource_id,
                "topic": "General",
                "subject": "General",
                "grade_level": 8,
                "started_at": now_utc,
                "last_heartbeat_at": now_utc,
                "accumulated_seconds": 0,
                "heartbeat_count": 0,
                "status": "active"
            }

        sess = cls._ACTIVE_SESSIONS[session_key]
        last_created = sess["last_heartbeat_at"]
        if last_created.tzinfo is None:
            last_created = last_created.replace(tzinfo=datetime.timezone.utc)
        elapsed_server_seconds = max(0.0, (now_utc - last_created).total_seconds())

        raw_dwell = max(0, int(request.dwell_seconds))

        if not request.is_active or elapsed_server_seconds < 2.0:
            verified_dwell = 0
        else:
            verified_dwell = min(raw_dwell, int(elapsed_server_seconds), 180)

        sess["last_heartbeat_at"] = now_utc
        sess["accumulated_seconds"] += verified_dwell
        sess["heartbeat_count"] += 1

        event = LearningEvent(
            student_user_id=student_id,
            content_item_id=request.resource_id if len(request.resource_id) == 36 else None,
            event_type="heartbeat",
            progress_percentage=min(90, int(sess["accumulated_seconds"] / 3)),
            verified_seconds=verified_dwell,
            heartbeat_count=sess["heartbeat_count"],
            client_timestamp=now_utc
        )
        db.add(event)
        db.commit()

        return SessionHeartbeatResponse(
            session_id=request.session_id,
            resource_id=request.resource_id,
            verified_seconds=verified_dwell,
            session_accumulated_seconds=sess["accumulated_seconds"],
            status="active",
            server_timestamp=now_utc.isoformat()
        )

    @classmethod
    def end_learning_session(
        cls,
        db: Session,
        student_user: Optional[User],
        request: SessionEndRequest
    ) -> SessionEndResponse:
        """
        Concludes a learning session, tallies total verified dwell time,
        and logs a completion event with appropriate gamification rewards.
        """
        if not student_user:
            raise ValueError("Student must be authenticated to conclude a learning session.")

        student_id = student_user.id
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        session_key = f"{student_id}:{request.session_id}"

        sess = cls._ACTIVE_SESSIONS.get(session_key, {
            "accumulated_seconds": 0,
            "heartbeat_count": 1,
            "resource_id": request.resource_id
        })
        total_seconds = sess.get("accumulated_seconds", 0)

        xp_awarded = 0
        if request.completed or total_seconds >= 180:
            xp_awarded = 25
            unique_key = f"xp:session_complete:{student_id}:{request.session_id}"
            ledger = RewardLedger(
                student_user_id=student_id,
                reward_type="CONTENT_COMPLETION_XP",
                xp_amount=xp_awarded,
                unique_reward_key=unique_key
            )
            db.add(ledger)
            profile = getattr(student_user, "student_profile", None)
            if profile:
                profile.xp_score = (profile.xp_score or 0) + xp_awarded

        event = LearningEvent(
            student_user_id=student_id,
            content_item_id=request.resource_id if len(request.resource_id) == 36 else None,
            event_type="completion_verified",
            progress_percentage=100,
            verified_seconds=total_seconds,
            heartbeat_count=sess.get("heartbeat_count", 1),
            client_timestamp=now_utc
        )
        db.add(event)
        db.commit()

        if session_key in cls._ACTIVE_SESSIONS:
            cls._ACTIVE_SESSIONS[session_key]["status"] = "completed"

        return SessionEndResponse(
            session_id=request.session_id,
            resource_id=request.resource_id,
            total_verified_seconds=total_seconds,
            xp_awarded=xp_awarded,
            status="completed",
            completed_at=now_utc.isoformat()
        )

    @classmethod
    def evaluate_pre_post_assessment(
        cls,
        db: Session,
        student_user: Optional[User],
        request: PrePostAssessmentSubmitRequest
    ) -> EmpiricalLearningGainOut:
        """
        Evaluates pre-test or post-test assessment and computes empirical learning gain.
        Computes Hake's normalized gain: g = (post - pre) / (100 - pre).
        Persists to EmpiricalLearningGainRecord for offline calibration (does not corrupt live ranking).
        """
        if not student_user:
            raise ValueError("Student must be authenticated to record empirical assessment gains.")

        student_id = student_user.id
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        intent = InterpretedIntent(
            subject=request.subject,
            topic=request.topic,
            grade_level=request.grade_level,
            board="CBSE",
            intent_type="explanation",
            depth_level="standard",
            format_preference="all",
            language="en",
            expanded_terms=[]
        )
        quiz_data = DiscoveryPipeline.generate_concept_check(intent)

        correct = 0
        total = max(1, len(quiz_data.questions))
        for q in quiz_data.questions:
            student_ans = request.answers.get(q.id)
            if student_ans is not None and student_ans == q.correct_option_index:
                correct += 1

        score_pct = round((correct / total) * 100.0, 1)

        pre_score = float(request.pre_test_score_pct if request.pre_test_score_pct is not None else score_pct)
        post_score = float(score_pct if request.assessment_stage == "post_test" else score_pct)

        raw_gain = round(post_score - pre_score, 1)
        if post_score >= pre_score:
            denominator = max(0.01, 100.0 - pre_score)
            normalized_gain = round(raw_gain / denominator, 4)
        else:
            denominator = max(0.01, pre_score)
            normalized_gain = round(raw_gain / denominator, 4)

        if normalized_gain >= 0.70:
            interpretation = "High normalized learning gain (g >= 0.70)"
        elif normalized_gain >= 0.30:
            interpretation = "Moderate normalized learning gain (0.30 <= g < 0.70)"
        elif normalized_gain >= 0.0:
            interpretation = "Low normalized learning gain (0.0 <= g < 0.30)"
        else:
            interpretation = "Negative learning gain (knowledge degradation)"

        session_key = f"{student_id}:{request.session_id or request.resource_id}"
        sess = cls._ACTIVE_SESSIONS.get(session_key, {})
        dwell_sec = sess.get("accumulated_seconds", 90)

        record = EmpiricalLearningGainRecord(
            student_user_id=student_id,
            resource_id=request.resource_id,
            session_id=request.session_id,
            topic=request.topic,
            subject=request.subject,
            pre_test_score_pct=pre_score,
            post_test_score_pct=post_score,
            raw_gain_pct=raw_gain,
            normalized_gain=normalized_gain,
            dwell_time_seconds=dwell_sec,
            created_at=now_utc
        )
        db.add(record)
        db.commit()

        return EmpiricalLearningGainOut(
            record_id=record.id,
            student_id=student_id,
            resource_id=request.resource_id,
            topic=request.topic,
            subject=request.subject,
            pre_test_score_pct=pre_score,
            post_test_score_pct=post_score,
            raw_gain_pct=raw_gain,
            normalized_gain=normalized_gain,
            interpretation=interpretation,
            dwell_time_seconds=dwell_sec,
            recorded_at=now_utc.isoformat()
        )

