import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.models.models import User, ContentItem, StudentProfile
from app.schemas.schemas import TutorAskRequest, TutorResponse
from app.core.security import RoleChecker
from app.safety.engine import SafetyEngine

router = APIRouter(prefix="/tutor", tags=["tutor"])

# Curriculum domain knowledge base for instant high-quality Socratic responses
TOPIC_TUTOR_INSIGHTS = {
    "quadratic equations": {
        "summary": "A quadratic equation is in the form ax² + bx + c = 0, where a ≠ 0. The discriminant D = b² - 4ac tells us whether roots are real and distinct (D > 0), equal (D = 0), or non-real (D < 0).",
        "analogy": "Think of throwing a basketball: the arc it travels in the air is a parabola, which can be modeled with a quadratic equation!",
        "follow_ups": [
            "What happens to the parabola's graph when 'a' is positive versus negative?",
            "Can you tell me what the discriminant value is if b² = 4ac?",
            "Would you like to solve an example problem together step-by-step?"
        ]
    },
    "human respiration": {
        "summary": "Respiration is the cellular biochemical process where glucose is oxidized in mitochondria with oxygen to release energy in the form of ATP molecules: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + 38 ATP.",
        "analogy": "Think of glucose as crude petroleum and ATP as refined electrical currency that your body's cellular machinery can actually spend!",
        "follow_ups": [
            "What is the difference between aerobic respiration and anaerobic fermentation?",
            "Where in the cell does glycolysis occur compared to the Krebs cycle?",
            "How do alveoli maximize the rate of oxygen gas exchange in the lungs?"
        ]
    },
    "python functions": {
        "summary": "Functions in Python are defined with the 'def' keyword. They take input arguments, execute a modular block of logic, and optionally 'return' a result. Variables defined inside a function have local scope.",
        "analogy": "A function is like a vending machine: you give it coins (arguments), it executes internal logic, and it dispenses your snack (return value) without you needing to know every gear turning inside!",
        "follow_ups": [
            "What is the difference between a parameter and an argument in Python?",
            "What does a Python function return by default if you don't write a return statement?",
            "How can default parameter values make your functions easier to reuse?"
        ]
    },
    "gravity": {
        "summary": "Newton's Law of Universal Gravitation states that every mass attracts every other mass with a force directly proportional to the product of their masses and inversely proportional to the square of the distance between them: F = G(m₁m₂)/r².",
        "analogy": "If you double your distance from a campfire, the heat drops by four times (inverse square law)—gravity acts across space with the exact same geometry!",
        "follow_ups": [
            "Why do astronauts on the Space Station float even though Earth's gravity there is still ~90% as strong?",
            "If Earth's mass doubled but its radius stayed the same, how would your weight change?",
            "What is the physical difference between 'mass' and 'weight'?"
        ]
    }
}

from app.ai.rag_engine import RAGEngine
from app.core.access_policy import require_ai_access
from app.core.age_policy import StudentAgePolicy

@router.post("/ask", response_model=TutorResponse)
def ask_ai_tutor(
    request: TutorAskRequest,
    current_user: User = Depends(require_ai_access),
    db: Session = Depends(get_db)
):
    """
    Interactive Socratic AI Tutor powered by curriculum RAG retrieval and safety hard gates.
    """
    # Determine student target age dynamically via centralized Age Policy
    target_age = StudentAgePolicy.get_student_age(current_user.student_profile if current_user.role == "student" else None)
    grade_lvl = current_user.student_profile.school_class.grade_level if (current_user.student_profile and current_user.student_profile.school_class) else 10

    # 1. Safety Hard Gate check on student's prompt
    safety_audit = SafetyEngine.audit_content(request.question, target_age=target_age)
    if not safety_audit["is_safe"]:
        return TutorResponse(
            answer="I am your Edufeedia Socratic study guide! I am designed to assist you with curriculum subjects, math, science, and coding concepts. Let's redirect our focus back to the lesson topic.",
            socratic_cue="What specific formula or idea in this module would you like to review?",
            follow_up_questions=["Can you explain the main definition in your own words?", "Would you like a simplified real-world example?"],
            is_safe=False
        )

    # 2. Query RAG Engine with Lesson Context & Semantic Retrieval
    rag_result = RAGEngine.query_rag_tutor(
        db=db,
        question=request.question,
        content_item_id=request.content_item_id,
        student_grade=grade_lvl
    )

    # 3. Output Safety Gate — Validate synthesized LLM response before returning to minor
    output_audit = SafetyEngine.audit_content(rag_result["answer"], target_age=target_age)
    if not output_audit["is_safe"]:
        return TutorResponse(
            answer="Let's focus on the foundational principles of this lesson. What core definition would you like to review together?",
            socratic_cue="Can you explain the problem in your own words?",
            follow_up_questions=["Would you like a step-by-step example?", "Which part seems challenging?"],
            is_safe=True
        )

    return TutorResponse(
        answer=rag_result["answer"],
        socratic_cue=rag_result["socratic_cue"],
        follow_up_questions=rag_result["follow_up_questions"],
        is_safe=True
    )
