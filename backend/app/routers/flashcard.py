from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import datetime

from app.database import get_db
from app.models.models import (
    User, Flashcard, StudentProfile, SpacedRepetitionSchedule
)
from app.schemas.schemas import (
    FlashcardOut, FlashcardReviewSubmit, FlashcardReviewResponse
)
from app.core.security import RoleChecker
from app.core.algorithms import calculate_sm2

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

@router.get("/deck", response_model=List[FlashcardOut])
def get_flashcard_deck(
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    grade = profile.school_class.grade_level if (profile and profile.school_class) else 10
    board = profile.board if profile else "CBSE"

    # 1. First get flashcards matching due spaced repetition topics
    today = datetime.date.today()
    due_schedules = db.query(SpacedRepetitionSchedule).filter(
        SpacedRepetitionSchedule.student_user_id == current_user.id,
        SpacedRepetitionSchedule.next_review_date <= today
    ).all()

    due_topics = [s.topic for s in due_schedules]
    
    deck = []
    if due_topics:
        due_cards = db.query(Flashcard).filter(
            Flashcard.topic.in_(due_topics),
            Flashcard.grade_level == grade
        ).all()
        deck.extend(due_cards)

    # 2. If deck has fewer than 6 cards, pad with general syllabus cards for student's grade/board
    if len(deck) < 6:
        existing_ids = [c.id for c in deck]
        padding_cards = db.query(Flashcard).filter(
            Flashcard.grade_level == grade,
            ~Flashcard.id.in_(existing_ids) if existing_ids else True
        ).limit(6 - len(deck)).all()
        deck.extend(padding_cards)

    # If still empty (e.g. no grade match), fallback to all available flashcards
    if not deck:
        deck = db.query(Flashcard).limit(6).all()

    return deck

@router.post("/review", response_model=FlashcardReviewResponse)
def submit_flashcard_review(
    review: FlashcardReviewSubmit,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    card = db.query(Flashcard).filter(Flashcard.id == review.flashcard_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    # Map review rating (1-4) to SM-2 quality (0-5)
    # 1: Again -> quality 1
    # 2: Hard  -> quality 2
    # 3: Good  -> quality 4
    # 4: Easy  -> quality 5
    quality_map = {1: 1, 2: 2, 3: 4, 4: 5}
    q = quality_map.get(review.rating, 3)

    # Find or initialize spaced repetition schedule
    schedule = db.query(SpacedRepetitionSchedule).filter(
        SpacedRepetitionSchedule.student_user_id == current_user.id,
        SpacedRepetitionSchedule.subject == card.subject,
        SpacedRepetitionSchedule.topic == card.topic
    ).first()

    if not schedule:
        interval, repetition, ef = calculate_sm2(q, 1, 0, 2.50)
        next_date = datetime.date.today() + datetime.timedelta(days=interval)
        schedule = SpacedRepetitionSchedule(
            student_user_id=current_user.id,
            subject=card.subject,
            topic=card.topic,
            interval_days=interval,
            repetition_number=repetition,
            easiness_factor=ef,
            next_review_date=next_date
        )
        db.add(schedule)
    else:
        interval, repetition, ef = calculate_sm2(
            q,
            schedule.interval_days,
            schedule.repetition_number,
            schedule.easiness_factor
        )
        next_date = datetime.date.today() + datetime.timedelta(days=interval)
        schedule.interval_days = interval
        schedule.repetition_number = repetition
        schedule.easiness_factor = ef
        schedule.next_review_date = next_date

    # Reward XP for active recall review
    xp_map = {1: 3, 2: 5, 3: 8, 4: 10}
    xp_earned = xp_map.get(review.rating, 5)

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if profile:
        profile.xp_score += xp_earned

    db.commit()

    messages = {
        1: "Review again soon to reinforce retention.",
        2: "Good effort! Interval adjusted for recall strengthening.",
        3: "Great memory recall! Spaced interval expanded.",
        4: "Superb mastery! Topic scheduled for future long-term recall."
    }

    return FlashcardReviewResponse(
        status="success",
        next_interval_days=interval,
        xp_earned=xp_earned,
        message=messages.get(review.rating, "Recall recorded successfully.")
    )
