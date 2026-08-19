from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import datetime

from app.database import get_db
from app.models.models import User, Quiz, Question, QuizAttempt, StudentProfile, SpacedRepetitionSchedule, ContentItem
from app.schemas.schemas import QuizOut, QuizSubmit, QuizAttemptOut
from app.core.security import get_current_user, RoleChecker
from app.core.algorithms import calculate_sm2

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.get("/content/{content_item_id}", response_model=QuizOut)
def get_quiz_by_content_item(
    content_item_id: str,
    current_user: User = Depends(RoleChecker(["student", "teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.content_item_id == content_item_id).first()
    if not quiz:
        # Match by topic if available
        item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
        if item:
            quiz = db.query(Quiz).join(ContentItem, Quiz.content_item_id == ContentItem.id).filter(ContentItem.topic == item.topic).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="No assessment quiz found for this lesson")
    return quiz

@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(
    quiz_id: str,
    current_user: User = Depends(RoleChecker(["student", "teacher", "school_admin"])),
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

    # Sync live database to owner's read-only Excel workbook
    try:
        from app.core.excel_exporter import sync_database_to_excel
        sync_database_to_excel(db)
    except Exception as e:
        print(f"[Excel Sync Warning]: {e}")
    
    return {
        "score": correct_count,
        "max_score": total_questions,
        "accuracy_percentage": accuracy,
        "xp_gained": xp_gained,
        "results": results
    }

from app.ai.question_generator import AIQuestionGenerator
from app.schemas.schemas import QuizGenerateRequest, QuizGenerateResponse, GeneratedQuestionOut, QuizCreateRequest

@router.post("/generate-draft", response_model=List[GeneratedQuestionOut])
def generate_ai_quiz_draft(
    request: QuizGenerateRequest,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Auto-generates draft assessment questions for teacher review and editing before publishing.
    """
    raw_questions = AIQuestionGenerator.generate_quiz_for_topic(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade_level or 10,
        num_questions=request.num_questions or 3
    )
    return [
        GeneratedQuestionOut(
            question_text=q["question_text"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            explanation=q["explanation"],
            difficulty=q.get("difficulty", "medium"),
            blooms_level=q.get("blooms_level", "Understand")
        ) for q in raw_questions
    ]

@router.post("/custom", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_custom_quiz(
    request: QuizCreateRequest,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Creates a teacher-authored or teacher-reviewed custom assessment with verified Bloom's taxonomy distribution.
    """
    if not request.questions or len(request.questions) == 0:
        raise HTTPException(status_code=400, detail="An assessment must contain at least one question")

    new_quiz = Quiz(
        content_item_id=request.content_item_id,
        title=request.title
    )
    db.add(new_quiz)
    db.flush()

    for q_data in request.questions:
        q_obj = Question(
            quiz_id=new_quiz.id,
            question_text=q_data.question_text,
            options=q_data.options,
            correct_answer=q_data.correct_answer,
            explanation=q_data.explanation,
            difficulty=q_data.difficulty
        )
        db.add(q_obj)

    db.commit()
    db.refresh(new_quiz)

    # Sync to Excel
    try:
        from app.core.excel_exporter import sync_database_to_excel
        sync_database_to_excel(db)
    except Exception as e:
        print(f"[Excel Sync Warning]: {e}")

    return new_quiz

@router.post("/generate", response_model=QuizGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_ai_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Auto-generates an assessment quiz set with Bloom's taxonomy difficulty, distractor explanations,
    and saves it to the database for instant interactive practice.
    """
    raw_questions = AIQuestionGenerator.generate_quiz_for_topic(
        subject=request.subject,
        topic=request.topic,
        grade=request.grade_level or 10,
        num_questions=request.num_questions or 3
    )

    # Persist the generated quiz
    new_quiz = Quiz(
        content_item_id=request.content_item_id,
        title=f"{request.topic} AI Concept Check"
    )
    db.add(new_quiz)
    db.flush()

    question_outs = []
    for q_data in raw_questions:
        q_obj = Question(
            quiz_id=new_quiz.id,
            question_text=q_data["question_text"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            difficulty=q_data.get("difficulty", "medium")
        )
        db.add(q_obj)
        question_outs.append(GeneratedQuestionOut(
            question_text=q_data["question_text"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            difficulty=q_data.get("difficulty", "medium"),
            blooms_level=q_data.get("blooms_level", "Understand")
        ))

    db.commit()

    # Sync to Excel
    try:
        from app.core.excel_exporter import sync_database_to_excel
        sync_database_to_excel(db)
    except Exception as e:
        print(f"[Excel Sync Warning]: {e}")

    return {
        "quiz_id": new_quiz.id,
        "title": new_quiz.title,
        "subject": request.subject,
        "topic": request.topic,
        "total_questions": len(question_outs),
        "questions": question_outs
    }
