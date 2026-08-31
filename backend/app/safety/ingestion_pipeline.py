"""
Multi-Stage Content Ingestion, Quarantine & Re-Quarantine Pipeline.
Enforces content-level screening, transcript extraction, safety validation,
provenance hash tracking, and automated re-screening upon upstream changes.
"""

import hashlib
import logging
import datetime
from typing import Dict, Any, Optional, List
from app.safety.engine import SafetyEngine
from app.safety.policy_engine import PolicyEngine

logger = logging.getLogger("edufeedia.ingestion")

CURRENT_SAFETY_POLICY_VERSION = "2026.2-DPDP"


class IngestionPipeline:
    """
    Manages the quarantine lifecycle for discovered and external educational content:
    DISCOVERED -> QUARANTINED -> AUTOMATED_SCREENING -> (APPROVED | NEEDS_HUMAN_REVIEW | REJECTED).
    Supports automated re-quarantine upon content drift or policy updates.
    """

    @classmethod
    def compute_content_hash(cls, title: str, description: str) -> str:
        payload = f"{title.strip().lower()}|{description.strip().lower()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def compute_transcript_hash(cls, transcript_text: Optional[str]) -> str:
        payload = (transcript_text or "").strip().lower()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def process_content_candidate(
        cls,
        title: str,
        description: str = "",
        transcript_text: Optional[str] = None,
        grade_level: int = 10,
        source_url: Optional[str] = None,
        source_platform: str = "NCERT",
        source_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive full-text and transcript safety screening on ingested material.
        Computes provenance hashes for continuous change detection.
        """
        c_hash = cls.compute_content_hash(title, description)
        t_hash = cls.compute_transcript_hash(transcript_text)

        # Step 1: Initial Ingestion & Quarantine Placement
        logger.info(f"[INGESTION QUARANTINE] Placing candidate '{title[:40]}' into quarantine for deep screening.")

        # Step 2: Automated Safety Audit (Adversarial, Toxicity, Under-18 Protection)
        target_age = grade_level + 5
        safety_audit = SafetyEngine.audit_content(
            title=title,
            description=f"{description} {transcript_text or ''}",
            tags=tags,
            target_age=target_age
        )

        provenance = {
            "source_platform": source_platform,
            "source_id": source_id,
            "source_url": source_url,
            "screened_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "policy_version": CURRENT_SAFETY_POLICY_VERSION
        }

        if not safety_audit.get("is_safe", True):
            logger.warning(f"[INGESTION REJECTED] Safety gate rejected content: {safety_audit.get('explanation')}")
            return {
                "moderation_status": "REJECTED",
                "is_approved": False,
                "safety_score": safety_audit.get("safety_score", 0),
                "edu_score": 0,
                "content_hash": c_hash,
                "transcript_hash": t_hash,
                "policy_version": CURRENT_SAFETY_POLICY_VERSION,
                "provenance_metadata": provenance,
                "reason": f"Safety screening failed: {safety_audit.get('explanation')}",
                "matched_rules": safety_audit.get("matched_rules", [])
            }

        # Step 3: Pedagogical Substance & Educational Density Check
        policy_engine = PolicyEngine()
        policy_eval = policy_engine.evaluate_content_submission(
            title=title,
            text=f"{description} \n {transcript_text or ''}",
            grade_level=grade_level,
            source_url=source_url
        )

        if not policy_eval.get("is_approved", True):
            logger.info(f"[INGESTION HUMAN REVIEW] Content held in quarantine for teacher review: {policy_eval.get('reason')}")
            return {
                "moderation_status": "NEEDS_HUMAN_REVIEW",
                "is_approved": False,
                "safety_score": safety_audit.get("safety_score", 100),
                "edu_score": int(policy_eval.get("edu_score", 0.3) * 100),
                "content_hash": c_hash,
                "transcript_hash": t_hash,
                "policy_version": CURRENT_SAFETY_POLICY_VERSION,
                "provenance_metadata": provenance,
                "reason": policy_eval.get("reason"),
                "matched_rules": []
            }

        # Step 4: Successful Full-Screening Approval
        logger.info(f"[INGESTION APPROVED] Candidate '{title[:40]}' passed all safety and pedagogical gates.")
        return {
            "moderation_status": "APPROVED",
            "is_approved": True,
            "safety_score": safety_audit.get("safety_score", 100),
            "edu_score": int(policy_eval.get("edu_score", 0.8) * 100),
            "content_hash": c_hash,
            "transcript_hash": t_hash,
            "policy_version": CURRENT_SAFETY_POLICY_VERSION,
            "provenance_metadata": provenance,
            "reason": "Passed automated full-corpus safety and pedagogical quality screening.",
            "matched_rules": []
        }

    @classmethod
    def rescreen_if_source_changed(
        cls,
        current_content_hash: Optional[str],
        current_transcript_hash: Optional[str],
        current_policy_version: Optional[str],
        new_title: str,
        new_description: str = "",
        new_transcript_text: Optional[str] = None,
        grade_level: int = 10,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detects if content, transcript, or policy has changed.
        If changes detected, triggers re-quarantine and re-screening.
        """
        new_c_hash = cls.compute_content_hash(new_title, new_description)
        new_t_hash = cls.compute_transcript_hash(new_transcript_text)

        content_changed = (new_c_hash != current_content_hash)
        transcript_changed = (new_t_hash != current_transcript_hash)
        policy_outdated = (current_policy_version != CURRENT_SAFETY_POLICY_VERSION)

        if not (content_changed or transcript_changed or policy_outdated):
            return {
                "needs_rescreening": False,
                "moderation_status": "APPROVED",
                "is_approved": True,
                "reason": "Content hash and policy version unchanged."
            }

        logger.warning(
            f"[CONTENT DRIFT DETECTED] Triggering re-quarantine for '{new_title[:40]}' "
            f"(Content Changed: {content_changed}, Transcript Changed: {transcript_changed}, Policy Outdated: {policy_outdated})"
        )

        rescreen_result = cls.process_content_candidate(
            title=new_title,
            description=new_description,
            transcript_text=new_transcript_text,
            grade_level=grade_level,
            source_url=source_url
        )
        rescreen_result["needs_rescreening"] = True
        return rescreen_result
