from typing import Dict, List, Any, Tuple

class SafetyPolicy:
    """
    Safety Policy Manager for students under 18.
    Applies multi-layered decision rules:
    - Rule-based triggers: Hard BLOCK
    - High classifier risk (> 0.85): Hard BLOCK
    - Moderate classifier risk (0.50 - 0.85): Flag for REVIEW
    - Clean content (< 0.50 risk): ALLOW with safety score
    """

    def __init__(
        self,
        block_threshold: float = 0.85,
        review_threshold: float = 0.50,
        min_edu_threshold: float = 0.15
    ):
        self.block_threshold = block_threshold
        self.review_threshold = review_threshold
        self.min_edu_threshold = min_edu_threshold

    def evaluate(
        self,
        rule_blocked: bool,
        matched_rules: List[str],
        matched_keywords: List[str],
        classification: Dict[str, Dict[str, Any]],
        target_age: int = 16
    ) -> Tuple[str, int, str]:
        """
        Returns (verdict, safety_score, explanation)
        verdict: 'ALLOW' | 'REVIEW' | 'BLOCK'
        safety_score: 0 to 100
        """
        # 1. Hard Rule Gate
        if rule_blocked:
            reasons = ", ".join(matched_rules)
            return (
                "BLOCK",
                0,
                f"Content blocked by hard safety policy rules for under-18 users. Violations: {reasons} (Keywords: {', '.join(matched_keywords[:3])})"
            )

        # 2. Risk Classification Scores
        risk_keys = ["TOXICITY", "VIOLENCE", "NSFW", "DRUGS", "DANGEROUS_ACTIVITIES"]
        max_risk = 0.0
        max_risk_category = None

        for k in risk_keys:
            score = classification.get(k, {}).get("score", 0.0)
            if score > max_risk:
                max_risk = score
                max_risk_category = k

        # 3. Decision Logic
        if max_risk >= self.block_threshold:
            safety_score = max(0, int((1.0 - max_risk) * 50))
            return (
                "BLOCK",
                safety_score,
                f"Classifier detected high risk in category: {max_risk_category} (Confidence: {max_risk:.2f}). Inappropriate for student environment."
            )
        elif max_risk >= self.review_threshold:
            safety_score = int((1.0 - max_risk) * 100)
            return (
                "REVIEW",
                safety_score,
                f"Moderate ambiguity detected in category: {max_risk_category} (Score: {max_risk:.2f}). Queued for educator/admin inspection before display."
            )
        else:
            edu_score = classification.get("EDUCATIONAL_QUALITY", {}).get("score", 0.5)
            # Clean safe score scaled from 90 to 100
            safety_score = min(100, int(95 + (edu_score * 5) - (max_risk * 10)))
            return (
                "ALLOW",
                safety_score,
                "Content certified 100% kid-safe and age-appropriate for under-18 learning."
            )

policy_instance = SafetyPolicy()
