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

from app.ai.rag_engine import RAGEngine
from app.core.access_policy import require_ai_access, AccessPolicy
from app.core.age_policy import StudentAgePolicy
from app.core.tenant_scope import TenantScope

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
    grade_lvl = (
        current_user.student_profile.school_class.grade_level
        if (current_user.student_profile and current_user.student_profile.school_class)
        else (current_user.student_profile.grade_level if current_user.student_profile else 10)
    )

    # 1. Safety Hard Gate check on student's prompt
    safety_audit = SafetyEngine.audit_content(request.question, target_age=target_age)
    if not safety_audit["is_safe"]:
        return TutorResponse(
            answer="I am your Edufeedia Socratic study guide! I am designed to assist you with curriculum subjects, math, science, and coding concepts. Let's redirect our focus back to the lesson topic.",
            socratic_cue="What specific formula or idea in this module would you like to review?",
            follow_up_questions=["Can you explain the main definition in your own words?", "Would you like a simplified real-world example?"],
            is_safe=False
        )

    # 2. Query RAG Engine with Lesson Context & Semantic Retrieval strictly within Tenant Scope
    valid_content_id = request.content_item_id
    if valid_content_id:
        ci = TenantScope.content(db, current_user).filter(
            ContentItem.id == valid_content_id,
            ContentItem.is_approved == True
        ).first()
        if not ci or not AccessPolicy.can_access_content_item(current_user, ci, db):
            valid_content_id = None

    board = current_user.student_profile.board if current_user.student_profile else "CBSE"
    rag_result = RAGEngine.query_rag_tutor(
        db=db,
        question=request.question,
        content_item_id=valid_content_id,
        student_grade=grade_lvl,
        student_id=current_user.id,
        board=board
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
        is_safe=True,
        grounding_source=rag_result.get("grounding_source"),
        subject=rag_result.get("subject"),
        topic=rag_result.get("topic"),
        curriculum_citations=rag_result.get("retrieved_chunks", [])
    )
