from typing import Dict, Any, List, Optional
from app.safety.rules import evaluate_rules
from app.safety.classifier import classify_text
from app.safety.policy import policy_instance

class SafetyEngine:
    """
    Unified Safety Engine acting as the First-Priority Hard Gate.
    Executes BEFORE candidate recommendation generation.
    """

    @classmethod
    def audit_content(
        cls,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        target_age: int = 16
    ) -> Dict[str, Any]:
        combined_text = f"{title} {description} {' '.join(tags or [])}".strip()

        # Step 1: Rule-based evaluation
        rule_blocked, matched_categories, matched_keywords = evaluate_rules(combined_text)

        # Step 2: Classifier prediction
        classification = classify_text(combined_text)

        # Step 3: Policy decision
        verdict, safety_score, explanation = policy_instance.evaluate(
            rule_blocked=rule_blocked,
            matched_rules=matched_categories,
            matched_keywords=matched_keywords,
            classification=classification,
            target_age=target_age
        )

        categories_list = []
        for cat_name, cat_data in classification.items():
            categories_list.append({
                "category": cat_name,
                "score": cat_data["score"],
                "severity": cat_data["severity"]
            })

        return {
            "verdict": verdict,
            "safety_score": safety_score,
            "is_safe": (verdict == "ALLOW"),
            "categories": categories_list,
            "matched_rules": matched_categories,
            "explanation": explanation
        }

    @classmethod
    def evaluate(cls, text: str, target_age: int = 16) -> Dict[str, Any]:
        """Convenience method to evaluate safety of an arbitrary text string."""
        return cls.audit_content(title=text, description="", target_age=target_age)

    @classmethod
    def is_safe_for_students(
        cls,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        target_age: int = 16
    ) -> bool:
        audit = cls.audit_content(title, description, tags, target_age)
        return audit["is_safe"]
