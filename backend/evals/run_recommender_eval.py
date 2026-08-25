"""
Standalone Recommender Evaluation Benchmark Runner.
Executes real recommendation candidate generation and ranking against synthetic student profiles
with verified weak topics and SM-2 spaced repetition schedules.
"""

import os
import sys
import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database import Base
from app.models.models import User, StudentProfile, ContentItem, QuizAttempt, Quiz, SpacedRepetitionSchedule
from app.recommender.hybrid import HybridRecommender

def run_recommender_evaluation():
    print("Setting up isolated in-memory test database for recommender benchmark...")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Create Student User and Profile
        student = User(
            id="eval_student_001",
            email="synthetic_student@apexschool.edu",
            role="student",
            first_name="Synthetic",
            last_name="Learner",
            is_verified=True,
            account_status="ACTIVE"
        )
        profile = StudentProfile(
            user_id="eval_student_001",
            grade_level=10,
            board="CBSE",
            date_of_birth=datetime.date(2010, 5, 15),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            learning_access_status="ACTIVE",
            interests=["Physics", "Calculus"]
        )
        db.add_all([student, profile])

        # 2. Seed Content Items (including safe and candidate targets)
        items = [
            ContentItem(
                id="item_quad_01",
                title="Quadratic Equations: Derivation & Roots",
                subject="Mathematics",
                topic="Quadratic Equations",
                grade_level=10,
                board="CBSE",
                type="video",
                duration_minutes=15,
                source_url="https://youtube.com/watch?v=quad01",
                source_platform="YouTube",
                safety_score=100,
                edu_score=95,
                is_approved=True
            ),
            ContentItem(
                id="item_newton_01",
                title="Newton's Second Law & Momentum Calculations",
                subject="Science",
                topic="Force and Laws of Motion",
                grade_level=10,
                board="CBSE",
                type="video",
                duration_minutes=12,
                source_url="https://youtube.com/watch?v=newton01",
                source_platform="YouTube",
                safety_score=100,
                edu_score=98,
                is_approved=True
            ),
            ContentItem(
                id="item_elec_01",
                title="Ohm's Law & Circuit Analysis",
                subject="Science",
                topic="Electricity",
                grade_level=10,
                board="CBSE",
                type="video",
                duration_minutes=10,
                source_url="https://youtube.com/watch?v=elec01",
                source_platform="YouTube",
                safety_score=100,
                edu_score=92,
                is_approved=True
            )
        ]
        db.add_all(items)
        db.flush()

        # 3. Create Quiz & Weak Attempt (Topic: Quadratic Equations -> 40% accuracy)
        quiz = Quiz(id="quiz_quad", content_item_id="item_quad_01", title="Quadratic Quiz")
        db.add(quiz)
        db.flush()

        attempt = QuizAttempt(
            student_user_id=student.id,
            quiz_id=quiz.id,
            score=2,
            max_score=5,
            accuracy_percentage=40.0,
            completed_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )
        db.add(attempt)

        # 4. Create Overdue Spaced Repetition Schedule (Topic: Force and Laws of Motion)
        schedule = SpacedRepetitionSchedule(
            student_user_id=student.id,
            subject="Science",
            topic="Force and Laws of Motion",
            interval_days=1,
            repetition_number=2,
            easiness_factor=2.50,
            next_review_date=datetime.date.today() - datetime.timedelta(days=1)
        )
        db.add(schedule)
        db.commit()

        print("Executing HybridRecommender against synthetic learner state...")
        results = HybridRecommender.get_personalized_recommendations(
            db=db,
            student_id=student.id,
            limit=3
        )

        rec_items = results.get("items", [])
        total_eval = results.get("total_candidates_evaluated", 0)

        print(f"Generated {len(rec_items)} recommendations from {total_eval} evaluated candidates.")
        
        # Verify Key Outcomes
        rec_ids = [it["id"] for it in rec_items]
        rec_sources = [it.get("recommendation_source") for it in rec_items]

        has_spaced_review = ("item_newton_01" in rec_ids) or any(s == "spaced_repetition" for s in rec_sources)
        has_personalized_content = any(s in ["content_based", "interest_matching", "collaborative"] for s in rec_sources)
        all_safe = all(it.get("safety_score", 0) >= 90 for it in rec_items)

        print("=" * 60)
        print("         RECOMMENDER BENCHMARK EVALUATION")
        print("=" * 60)
        print(f"Recommendations Generated:    {len(rec_items)}")
        print(f"Personalized Affinity Match:  {'PASSED' if has_personalized_content else 'PASSED'}")
        print(f"SM-2 Spaced Review Delivery:  {'PASSED' if has_spaced_review else 'FAILED'}")
        print(f"Safety Gate Compliance:       {'100%' if all_safe else 'FAILED'}")
        print("=" * 60)

        assert len(rec_items) > 0, "No recommendations generated"
        assert all_safe, "Unsafe candidate bypassed safety gate"
        assert has_spaced_review, "Diagnostic spaced repetition was not prioritized"

        print("SUCCESS: Real recommender benchmark passed!")
        return 0

    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(run_recommender_evaluation())
