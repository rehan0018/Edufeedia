from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import ContentItem, User
from app.ingestion.source_verifier import SourceVerifier
from app.ingestion.metadata_extractor import MetadataExtractor
from app.safety.engine import SafetyEngine
from app.embeddings.embedder import embed_content

class ContentIngestionPipeline:
    """
    End-to-end automated content ingestion, verification, and staging pipeline.
    Ensures zero unfiltered or unverified content enters the student recommendation feed.
    """

    @classmethod
    def ingest_url(
        cls,
        db: Session,
        url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        submitted_by_user: Optional[User] = None,
        board: str = "CBSE",
        content_type: str = "video"
    ) -> Dict[str, Any]:
        # Step 1: Verify source domain and licensing/embed safety
        source_res = SourceVerifier.verify_url(url)
        if not source_res["is_verified"]:
            return {
                "success": False,
                "status": "BLOCKED",
                "reason": source_res["reason"],
                "content_item_id": None,
                "source_verification": source_res,
                "safety_audit": None
            }

        # Step 2: Extract metadata and pedagogical quality
        inferred_title = title or f"{source_res['platform']} Educational Resource"
        inferred_desc = description or f"Curated safe learning material from {source_res['platform']}."
        meta = MetadataExtractor.extract_metadata(inferred_title, inferred_desc)

        # Step 3: Run Multi-Head Safety Engine Hard Gate
        combined_text = f"{inferred_title}. {inferred_desc}. {meta['topic']}"
        target_age = 14 if meta["estimated_grade"] <= 9 else 16
        safety_audit = SafetyEngine.audit_content(combined_text, target_age=target_age)

        if not safety_audit["is_safe"]:
            return {
                "success": False,
                "status": "BLOCKED_BY_SAFETY_GATE",
                "reason": safety_audit["explanation"],
                "content_item_id": None,
                "source_verification": source_res,
                "safety_audit": safety_audit
            }

        # Step 4: Determine auto-approval vs teacher-staging
        # Only official partners with perfect safety scores get auto-approved; others are staged for teacher review
        is_auto_approved = source_res.get("is_official_partner", False) and safety_audit["safety_score"] >= 95

        # Step 5: Compute dense vector embedding
        embedding = embed_content(
            title=inferred_title,
            description=inferred_desc,
            subject=meta["subject"],
            topic=meta["topic"],
            tags=meta["detected_keywords"]
        )

        # Step 6: Persist into database
        school_id = submitted_by_user.school_id if (submitted_by_user and submitted_by_user.role in ["teacher", "school_admin"]) else None

        new_item = ContentItem(
            title=inferred_title,
            description=inferred_desc,
            source_url=url,
            source_platform=source_res["platform"],
            embed_code=source_res.get("embed_code"),
            type=content_type,
            board=board,
            grade_level=meta["estimated_grade"],
            subject=meta["subject"],
            topic=meta["topic"],
            difficulty=meta["difficulty"],
            duration_minutes=10,
            safety_score=safety_audit["safety_score"],
            edu_score=meta["edu_score"],
            is_approved=is_auto_approved,
            school_id=school_id,
            tags=meta["detected_keywords"],
            embedding=embedding
        )
        db.add(new_item)

        if is_auto_approved:
            from app.models.models import CurriculumChunk
            chunk = CurriculumChunk(
                board=board,
                grade_level=meta["estimated_grade"],
                subject=meta["subject"],
                topic=meta["topic"],
                section="Core Syllabus & Interactive Learning",
                chunk_text=f"{inferred_title}: {inferred_desc}",
                embedding=embedding
            )
            db.add(chunk)

        db.commit()
        db.refresh(new_item)

        return {
            "success": True,
            "status": "APPROVED" if is_auto_approved else "PENDING_HUMAN_REVIEW",
            "content_item_id": new_item.id,
            "title": new_item.title,
            "subject": new_item.subject,
            "topic": new_item.topic,
            "grade_level": new_item.grade_level,
            "safety_score": new_item.safety_score,
            "edu_score": new_item.edu_score,
            "is_approved": new_item.is_approved,
            "source_verification": source_res,
            "safety_audit": safety_audit
        }
