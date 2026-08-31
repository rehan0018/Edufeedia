"""
Multi-Stage Content Ingestion & Quarantine Pipeline.
Enforces content-level screening, transcript extraction, safety validation,
and automated quarantine gating before publishing external resources to students.
"""

import logging
from typing import Dict, Any, Optional, List
from app.safety.engine import SafetyEngine
from app.safety.policy_engine import PolicyEngine

logger = logging.getLogger("edufeedia.ingestion")


class IngestionPipeline:
    """
    Manages the quarantine lifecycle for discovered and external educational content:
    DISCOVERED -> QUARANTINED -> AUTOMATED_SCREENING -> (APPROVED | NEEDS_HUMAN_REVIEW | REJECTED).
    """

    @classmethod
    def process_content_candidate(
        cls,
        title: str,
        description: str = "",
        transcript_text: Optional[str] = None,
        grade_level: int = 10,
        source_url: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive full-text and transcript safety screening on ingested material.
        """
        # Step 1: Initial Ingestion & Quarantine Placement
        lifecycle_state = "QUARANTINED"
        logger.info(f"[INGESTION QUARANTINE] Placing candidate '{title[:40]}' into quarantine for deep screening.")

        # Step 2: Assemble Full Content Corpus (Metadata + Full Video Transcript)
        full_corpus_pieces = [title, description]
        if transcript_text:
            full_corpus_pieces.append(transcript_text)
        if tags:
            full_corpus_pieces.extend(tags)
        full_corpus = " \n".join(full_corpus_pieces)

        # Step 3: Automated Safety Audit (Adversarial, Toxicity, Under-18 Protection)
        target_age = grade_level + 5
        safety_audit = SafetyEngine.audit_content(
            title=title,
            description=f"{description} {transcript_text or ''}",
            tags=tags,
            target_age=target_age
        )

        if not safety_audit.get("is_safe", True):
            logger.warning(f"[INGESTION REJECTED] Safety gate rejected content: {safety_audit.get('explanation')}")
            return {
                "moderation_status": "REJECTED",
                "is_approved": False,
                "safety_score": safety_audit.get("safety_score", 0),
                "edu_score": 0,
                "reason": f"Safety screening failed: {safety_audit.get('explanation')}",
                "matched_rules": safety_audit.get("matched_rules", [])
            }

        # Step 4: Pedagogical Substance & Educational Density Check
        policy_engine = PolicyEngine()
        policy_eval = policy_engine.evaluate_content_submission(
            title=title,
            text=f"{description} \n {transcript_text or ''}",
            grade_level=grade_level,
            source_url=source_url
        )

        if not policy_eval.get("is_approved", True):
            # If rejected due to low educational depth or borderline quality -> Hold in quarantine for human teacher review
            logger.info(f"[INGESTION HUMAN REVIEW] Content held in quarantine for teacher review: {policy_eval.get('reason')}")
            return {
                "moderation_status": "NEEDS_HUMAN_REVIEW",
                "is_approved": False,
                "safety_score": safety_audit.get("safety_score", 100),
                "edu_score": int(policy_eval.get("edu_score", 0.3) * 100),
                "reason": policy_eval.get("reason"),
                "matched_rules": []
            }

        # Step 5: Successful Full-Screening Approval
        logger.info(f"[INGESTION APPROVED] Candidate '{title[:40]}' passed all safety and pedagogical gates.")
        return {
            "moderation_status": "APPROVED",
            "is_approved": True,
            "safety_score": safety_audit.get("safety_score", 100),
            "edu_score": int(policy_eval.get("edu_score", 0.8) * 100),
            "reason": "Passed automated full-corpus safety and pedagogical quality screening.",
            "matched_rules": []
        }
