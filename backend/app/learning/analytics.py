from sqlalchemy.orm import Session
from typing import Dict, List, Any
import datetime

from app.models.models import QuizAttempt, Quiz, ContentItem, SpacedRepetitionSchedule, StudentProfile
from app.core.algorithms import calculate_sm2

class StudentAnalyticsEngine:
    @staticmethod
    def get_student_mastery_report(db: Session, student_id: str) -> Dict[str, Any]:
        return compute_student_topic_mastery(db, student_id)

def compute_student_topic_mastery(db: Session, student_id: str) -> Dict[str, Any]:
    """
    Analyzes student quiz attempts, computes topic-level mastery rates,
    identifies weak topics (<60% accuracy), and schedules remedial SM-2 revision.
    """
    attempts = db.query(QuizAttempt).filter(QuizAttempt.student_user_id == student_id).all()

    topic_stats: Dict[str, Dict[str, Any]] = {}

    for attempt in attempts:
        quiz = attempt.quiz
        if not quiz:
            continue
        topic = "General Knowledge"
        subject = "General"

        if quiz.content_item:
            topic = quiz.content_item.topic
            subject = quiz.content_item.subject
        elif quiz.title:
            topic = quiz.title.replace(" Quiz", "")

        if topic not in topic_stats:
            topic_stats[topic] = {
                "subject": subject,
                "topic": topic,
                "total_attempts": 0,
                "total_score": 0,
                "total_max": 0,
                "accuracy_percentage": 0.0,
                "is_weak": False,
                "status": "Proficient"
            }

        topic_stats[topic]["total_attempts"] += 1
        topic_stats[topic]["total_score"] += attempt.score
        topic_stats[topic]["total_max"] += attempt.max_score

    # Calculate percentages
    weak_topics = []
    strong_topics = []
    remedial_queued = []

    today = datetime.date.today()

    for topic_name, data in topic_stats.items():
        if data["total_max"] > 0:
            acc = (data["total_score"] / data["total_max"]) * 100.0
            data["accuracy_percentage"] = round(acc, 1)

            if acc < 60.0:
                data["is_weak"] = True
                data["status"] = "Needs Practice"
                weak_topics.append(data)

                # Automatically ensure an SM-2 spaced repetition schedule exists for this weak topic
                existing_schedule = db.query(SpacedRepetitionSchedule).filter(
                    SpacedRepetitionSchedule.student_user_id == student_id,
                    SpacedRepetitionSchedule.topic == topic_name
                ).first()

                if not existing_schedule:
                    # Queue priority review for tomorrow
                    new_sched = SpacedRepetitionSchedule(
                        student_user_id=student_id,
                        subject=data["subject"],
                        topic=topic_name,
                        interval_days=1,
                        repetition_number=0,
                        easiness_factor=2.00, # Lower easiness factor for challenging topics
                        next_review_date=today + datetime.timedelta(days=1)
                    )
                    db.add(new_sched)
                    remedial_queued.append(topic_name)
                elif existing_schedule.next_review_date > today + datetime.timedelta(days=2):
                    # Pull forward revision due date for weak topics
                    existing_schedule.next_review_date = today + datetime.timedelta(days=1)
                    existing_schedule.easiness_factor = max(1.30, float(existing_schedule.easiness_factor) - 0.20)
                    remedial_queued.append(topic_name)
            else:
                data["status"] = "Mastered" if acc >= 85.0 else "Good"
                strong_topics.append(data)

    if remedial_queued:
        db.commit()

    # Overall subject breakdown
    subject_scores: Dict[str, Dict[str, float]] = {}
    for data in topic_stats.values():
        sub = data["subject"]
        if sub not in subject_scores:
            subject_scores[sub] = {"score": 0, "max": 0}
        subject_scores[sub]["score"] += data["total_score"]
        subject_scores[sub]["max"] += data["total_max"]

    subject_mastery = []
    for sub, scores in subject_scores.items():
        pct = (scores["score"] / scores["max"] * 100.0) if scores["max"] > 0 else 100.0
        subject_mastery.append({
            "subject": sub,
            "mastery_percentage": round(pct, 1),
            "level": "Excellent" if pct >= 80 else ("Moderate" if pct >= 60 else "Attention Required")
        })

    return {
        "student_id": student_id,
        "total_topics_evaluated": len(topic_stats),
        "weak_topic_count": len(weak_topics),
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "all_topics": list(topic_stats.values()),
        "subject_mastery": subject_mastery,
        "remedial_schedules_activated": remedial_queued
    }
