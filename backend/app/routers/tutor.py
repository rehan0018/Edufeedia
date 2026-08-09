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

@router.post("/ask", response_model=TutorResponse)
def ask_ai_tutor(
    request: TutorAskRequest,
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent"])),
    db: Session = Depends(get_db)
):
    """
    Interactive Socratic AI Tutor providing student-safe, encouraging concept explanations.
    """
    # 1. Safety Hard Gate check on student's prompt
    safety_audit = SafetyEngine.audit_content(request.question, target_age=16)
    if not safety_audit["is_safe"]:
        return TutorResponse(
            answer="I am your Edufeedia Socratic study guide! I am designed to assist you with curriculum subjects, math, science, and coding concepts. Let's redirect our focus back to the lesson topic.",
            socratic_cue="What specific formula or idea in this module would you like to review?",
            follow_up_questions=["Can you explain the main definition in your own words?", "Would you like a simplified real-world example?"],
            is_safe=False
        )

    # 2. Retrieve Content Context
    content = db.query(ContentItem).filter(ContentItem.id == request.content_item_id).first()
    topic_key = content.topic.lower() if content else "general"

    # Match predefined domain knowledge or construct generalized pedagogical explanation
    matched_insight = None
    for k, v in TOPIC_TUTOR_INSIGHTS.items():
        if k in topic_key or (content and k in content.title.lower()):
            matched_insight = v
            break

    q_lower = request.question.lower()

    if matched_insight:
        if "example" in q_lower or "analogy" in q_lower or "simple" in q_lower:
            answer = f"💡 **Intuitive Analogy**: {matched_insight['analogy']}\n\n**Concept Review**: {matched_insight['summary']}"
            socratic_cue = "Does visualizing it this way make the mechanics clearer?"
        elif "formula" in q_lower or "equation" in q_lower or "how" in q_lower:
            answer = f"📐 **Key Formula & Definition**: {matched_insight['summary']}"
            socratic_cue = "Try plugging in a test value to see how the variables balance out!"
        else:
            answer = f"Hello {current_user.first_name}! Regarding **{content.topic if content else 'this concept'}**:\n\n{matched_insight['summary']}\n\n💡 *Analogy*: {matched_insight['analogy']}"
            socratic_cue = "What is the very first step you'd take when applying this concept?"

        follow_ups = matched_insight["follow_ups"]
    else:
        topic_name = content.topic if content else "this curriculum topic"
        subject_name = content.subject if content else "General Studies"
        answer = f"Great question, {current_user.first_name}! In **{subject_name} ({topic_name})**, the fundamental principle revolves around breaking down complex equations or processes into simple, verifiable components.\n\nTake it one step at a time: identify the given variables, state your known relationships, and verify your answer against boundary conditions."
        socratic_cue = f"Can you identify what the primary knowns and unknowns are in {topic_name}?"
        follow_ups = [
            f"What is the core definition of {topic_name} in your textbook?",
            "Would you like to test your understanding with a quick practice question?",
            "How does this connect with what we covered in previous chapters?"
        ]

    return TutorResponse(
        answer=answer,
        socratic_cue=socratic_cue,
        follow_up_questions=follow_ups,
        is_safe=True
    )
