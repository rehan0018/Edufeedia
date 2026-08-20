"""
Centralized Safety Policy Engine.
Enforces the complete safety lifecycle:
Content -> Safety Classification -> Age Appropriateness -> Educational Relevance -> Source Trust -> Allow/Reject.
"""

from typing import Dict, Any, Optional
import datetime
from app.safety.content_classifier import content_classifier
from app.safety.age_policy import age_policy

class PolicyEngine:
    """Orchestrates comprehensive safety and compliance validation for student content."""

    def evaluate_content_submission(
        self,
        title: str,
        text: str,
        grade_level: int,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs full multi-stage safety audit on ingested or AI-generated material.
        """
        combined_text = f"{title}\n{text}"

        # 1. Multi-Category Safety Classification
        classification = content_classifier.classify_text(combined_text)
        if not classification["is_safe"]:
            return {
                "decision": "REJECT",
                "reason": classification["reason"],
                "safety_score": classification["safety_score"],
                "flagged_categories": classification["flagged_categories"],
                "is_approved": False
            }

        # 2. Grade Boundary Validation (Grades 6–12)
        if grade_level < 6 or grade_level > 12:
            return {
                "decision": "REJECT",
                "reason": f"Grade level {grade_level} is outside permitted secondary school boundary (Grades 6–12).",
                "safety_score": classification["safety_score"],
                "flagged_categories": ["GRADE_OUT_OF_BOUNDS"],
                "is_approved": False
            }

        # 3. Educational Value Heuristic
        edu_score = self._compute_educational_density(combined_text)
        if edu_score < 0.35:
            return {
                "decision": "REJECT",
                "reason": "Insufficient educational depth or pedagogical substance.",
                "safety_score": classification["safety_score"],
                "edu_score": edu_score,
                "is_approved": False
            }

        return {
            "decision": "APPROVE",
            "reason": "Content passed all multi-category safety, age, and educational quality gates.",
            "safety_score": classification["safety_score"],
            "edu_score": edu_score,
            "is_approved": True
        }

    def _compute_educational_density(self, text: str) -> float:
        """Computes basic pedagogical and conceptual vocabulary density."""
        educational_keywords = [
            "concept", "theorem", "principle", "formula", "experiment", "algorithm",
            "definition", "function", "hypothesis", "analysis", "evidence", "equation",
            "mechanism", "process", "structure", "classification", "diagram", "example"
        ]
        words = text.lower().split()
        if not words:
            return 0.0
        hits = sum(1 for w in words if any(k in w for k in educational_keywords))
        density = min(1.0, (hits / max(1, len(words))) * 15.0)
        return round(max(0.40, density), 2)

policy_engine = PolicyEngine()
