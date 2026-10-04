"""
Student-Aware Personalized Reranker.
Adjusts candidate ranking based on student's active knowledge state,
historical weak topics, mastery trajectory, and preferred sensory format.
"""

from typing import List, Dict, Any, Optional
from app.schemas.schemas import InterpretedIntent, QualityScoreBreakdown

class PersonalizedReranker:
    """
    Reranks educational candidates using student knowledge state,
    weak-topic bridging needs, and cognitive format preferences.
    """

    @classmethod
    def rerank_candidates(
        cls,
        scored_candidates: List[Dict[str, Any]],
        intent: InterpretedIntent,
        student_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not scored_candidates:
            return []

        ctx = student_context or {}
        preferred_format = ctx.get("preferred_format") or intent.format_preference
        weak_topics = [t.lower() for t in ctx.get("weak_topics", [])]
        topic_mastery = float(ctx.get("topic_mastery", 0.70))  # Default 70% baseline

        reranked = []
        for cand in scored_candidates:
            base_score = float(cand.get("quality_score", 0.80))
            multiplier = 1.0

            # 1. Format Preference Alignment
            res_type = cand.get("resource_type", "")
            if preferred_format and res_type == preferred_format:
                multiplier += 0.08
            elif res_type == "animation" and (ctx.get("prefers_visual") or topic_mastery < 0.65):
                # Students struggling or with visual preference gain significantly from animated Socratic modeling
                multiplier += 0.07

            # 2. Weak Topic Remediation Boost
            is_weak_topic = any(cand.get("topic", "").lower() in wt or wt in cand.get("topic", "").lower() for wt in weak_topics)
            if is_weak_topic:
                # Prioritize high-pedagogy interactive simulations and foundational animations
                if res_type in ["interactive_sim", "animation", "reading"]:
                    multiplier += 0.09
                cand["why_chosen_personalized"] = "Recommended to reinforce understanding based on your recent practice."

            # 3. Cognitive Level Match
            if topic_mastery > 0.85 and cand.get("duration_minutes", 0) > 10:
                # Mastery student ready for deeper, comprehensive video
                multiplier += 0.05
            elif topic_mastery < 0.60 and cand.get("duration_minutes", 0) <= 7:
                # Foundational student benefits from bite-sized, high-yield concept chunks
                multiplier += 0.06

            personalized_score = min(1.00, round(base_score * multiplier, 2))
            cand["personalized_score"] = personalized_score
            reranked.append(cand)

        # Sort descending by personalized score
        reranked.sort(key=lambda x: x.get("personalized_score", 0), reverse=True)
        return reranked
