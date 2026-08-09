from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import datetime

from app.database import get_db
from app.models.models import User, Quiz, Question, QuizAttempt, StudentProfile, SpacedRepetitionSchedule
from app.schemas.schemas import QuizOut, QuizSubmit, QuizAttemptOut
from app.core.security import get_current_user, RoleChecker
from app.core.algorithms import calculate_sm2

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(
    quiz_id: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

@router.post("/submit", response_model=Dict[str, Any])
def submit_quiz(
    submission: QuizSubmit,
    current_user: User = Depends(RoleChecker(["student"])),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    questions = {q.id: q for q in quiz.questions}
    if not questions:
        raise HTTPException(status_code=400, detail="Quiz has no questions")
        
    correct_count = 0
    total_questions = len(questions)
    results = []
    
    for ans in submission.answers:
        question = questions.get(ans.question_id)
        if not question:
            continue
            
        is_correct = (question.correct_answer.strip().lower() == ans.selected_answer.strip().lower())
        if is_correct:
            correct_count += 1
            
        results.append({
            "question_id": question.id,
            "selected_answer": ans.selected_answer,
            "correct_answer": question.correct_answer,
            "is_correct": is_correct,
            "explanation": question.explanation
        })
        
    accuracy = (correct_count / total_questions) * 100.0
    
    # Store attempt
    attempt = QuizAttempt(
        student_user_id=current_user.id,
        quiz_id=quiz.id,
        score=correct_count,
        max_score=total_questions,
        accuracy_percentage=accuracy
    )
    db.add(attempt)
    
    # Reward XP
    xp_gained = correct_count * 5 # 5 XP per correct answer
    if accuracy == 100.0:
        xp_gained += 25 # 25 XP bonus for 100% score
        
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if profile:
        profile.xp_score += xp_gained
        
    # Spaced Repetition (SM-2) Interval Calculation
    # Scale accuracy to 0-5 response quality grade
    if accuracy >= 100.0:
        q = 5
    elif accuracy >= 80.0:
        q = 4
    elif accuracy >= 60.0:
        q = 3
    elif accuracy >= 40.0:
        q = 2
    elif accuracy >= 20.0:
        q = 1
    else:
        q = 0
        
    # Find active spaced repetition schedule for this quiz subject/topic
    if quiz.content_item:
        item = quiz.content_item
        schedule = db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == current_user.id,
            SpacedRepetitionSchedule.subject == item.subject,
            SpacedRepetitionSchedule.topic == item.topic
        ).first()
        
        if not schedule:
            # Create a fresh schedule starting with SM-2 defaults
            interval, repetition, ef = calculate_sm2(q, 1, 0, 2.50)
            tomorrow = datetime.date.today() + datetime.timedelta(days=interval)
            schedule = SpacedRepetitionSchedule(
                student_user_id=current_user.id,
                subject=item.subject,
                topic=item.topic,
                interval_days=interval,
                repetition_number=repetition,
                easiness_factor=ef,
                next_review_date=tomorrow
            )
            db.add(schedule)
        else:
            # Update existing schedule parameters
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
            
    db.commit()
    
    return {
        "score": correct_count,
        "max_score": total_questions,
        "accuracy_percentage": accuracy,
        "xp_gained": xp_gained,
        "results": results
    }
