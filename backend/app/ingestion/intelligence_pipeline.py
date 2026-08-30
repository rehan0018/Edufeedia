import hashlib
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import datetime

from app.models.models import IngestedSource, ContentItem, CurriculumChunk
from app.ingestion.source_verifier import SourceVerifier
from app.ingestion.metadata_extractor import MetadataExtractor
from app.safety.engine import SafetyEngine
from app.embeddings.embedder import embed_content

class ContentIntelligencePipeline:
    """
    Edufeedia Content Intelligence & Ingestion Pipeline:
    1. Source Verification & Platform Whitelisting
    2. Canonical URL & SHA-256 Deduplication
    3. Metadata, Curriculum Syllabus & Pedagogical Quality Extraction
    4. Multi-Head Safety Moderation Gating
    5. Automatic Educational Chunking & 384-d Vector Embedding
    6. Database Staging for Human/Teacher Review
    """

    @classmethod
    def compute_sha256(cls, text: str) -> str:
        clean = text.strip().lower()
        return hashlib.sha256(clean.encode('utf-8')).hexdigest()

    @classmethod
    def process_and_stage_source(
        cls,
        db: Session,
        url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        raw_text: Optional[str] = None,
        submitted_by: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Source Verification
        verification = SourceVerifier.verify_url(url)
        if not verification["is_trusted"]:
            return {
                "success": False,
                "error": "UNTRUSTED_SOURCE",
                "message": f"Source rejected: {verification.get('reason', 'Domain not permitted.')}",
                "platform": verification.get("platform", "unknown")
            }

        # 2. Canonical Deduplication via SHA-256
        url_digest = cls.compute_sha256(url)
        existing = db.query(IngestedSource).filter(IngestedSource.url_hash == url_digest).first()
        if existing:
            return {
                "success": True,
                "is_duplicate": True,
                "source_id": existing.id,
                "status": existing.status,
                "message": "Resource already indexed in Edufeedia staging queue.",
                "curriculum_code": existing.curriculum_code
            }

        # 3. Live Adapter Metadata Fetching
        from app.ingestion.adapters.factory import ContentFetcherFactory
        adapter_fetch = ContentFetcherFactory.fetch(url)
        fetched_title = adapter_fetch.get("title") if adapter_fetch.get("success") else None

        # Resolve title & text
        final_title = title or fetched_title or f"Educational Resource from {verification['platform'].capitalize()}"
        final_desc = description or ""
        final_text = raw_text or f"{final_title}. {final_desc}"

        # 4. Metadata & Pedagogical Extraction
        metadata = MetadataExtractor.extract_metadata(
            title=final_title,
            description=final_desc,
            raw_text=final_text
        )

        # 4. Multi-Head Safety Audit
        safety_audit = SafetyEngine.audit_content(
            f"{final_title}. {final_desc}. {final_text[:300]}",
            target_age=metadata["estimated_grade"] + 5
        )

        # 5. Determine Initial Staging Status
        initial_status = "pending_review"
        if not safety_audit["is_safe"]:
            initial_status = "rejected"

        # 6. Save Ingested Source Record
        staged_record = IngestedSource(
            source_url=url,
            url_hash=url_digest,
            source_platform=verification["platform"],
            title=final_title,
            description=final_desc,
            raw_text=final_text,
            subject=metadata["subject"],
            topic=metadata["topic"],
            grade_level=metadata["estimated_grade"],
            board="CBSE",
            curriculum_code=metadata.get("curriculum_code"),
            status=initial_status,
            safety_audit=safety_audit,
            edu_score=metadata["edu_score"],
            submitted_by=submitted_by
        )
        db.add(staged_record)
        db.commit()
        db.refresh(staged_record)

        return {
            "success": True,
            "is_duplicate": False,
            "source_id": staged_record.id,
            "status": staged_record.status,
            "platform": staged_record.source_platform,
            "subject": staged_record.subject,
            "topic": staged_record.topic,
            "curriculum_code": staged_record.curriculum_code,
            "estimated_grade": staged_record.grade_level,
            "edu_score": staged_record.edu_score,
            "safety_verdict": safety_audit["verdict"],
            "embed_code": verification.get("embed_code"),
            "message": "Resource successfully ingested and staged for review."
        }

    @classmethod
    def approve_and_index_source(
        cls,
        db: Session,
        source_id: str,
        reviewer: Any = None,
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        actual_reviewer = reviewer if reviewer is not None else (reviewer_id or "system_admin")
        actual_reviewer_id = actual_reviewer.id if hasattr(actual_reviewer, "id") else str(actual_reviewer)
        if hasattr(actual_reviewer, "role") and actual_reviewer.role not in ["teacher", "school_admin", "admin", "super_admin"]:
            raise PermissionError("Unauthorized content approval attempt: caller lacks educational moderator credentials.")

        source = db.query(IngestedSource).filter(IngestedSource.id == source_id).first()
        if not source:
            return {"success": False, "message": "Ingested source not found."}

        # 1. Update IngestedSource Status
        source.status = "approved"
        source.reviewed_by = actual_reviewer_id
        source.reviewed_at = datetime.datetime.now(datetime.timezone.utc)

        # 2. Generate 384-d Embedding
        embedding_vec = embed_content(
            title=source.title,
            description=source.description or "",
            subject=source.subject or "General",
            topic=source.topic or "Review",
            tags=[source.subject, source.topic, source.board]
        )

        # 3. Create Live ContentItem in Catalog
        content_item = ContentItem(
            title=source.title,
            description=source.description,
            source_url=source.source_url,
            source_platform=source.source_platform,
            embed_code=SourceVerifier.verify_url(source.source_url).get("embed_code"),
            type="video" if source.source_platform == "youtube" else "interactive",
            board=source.board or "CBSE",
            grade_level=source.grade_level or 10,
            subject=source.subject or "General",
            topic=source.topic or "Concept",
            difficulty="medium",
            duration_minutes=10,
            safety_score=source.safety_audit.get("safety_score", 95) if source.safety_audit else 95,
            edu_score=source.edu_score or 85,
            is_approved=True,
            embedding=embedding_vec
        )
        db.add(content_item)

        # 4. Create Searchable Curriculum Knowledge Chunk
        chunk = CurriculumChunk(
            board=source.board or "CBSE",
            grade_level=source.grade_level or 10,
            subject=source.subject or "General",
            topic=source.topic or "Concept",
            section="Ingested Lesson Overview",
            curriculum_code=source.curriculum_code,
            chunk_text=f"{source.title}: {source.raw_text or source.description}",
            embedding=embedding_vec
        )
        db.add(chunk)

        db.commit()
        db.refresh(content_item)

        return {
            "success": True,
            "content_item_id": content_item.id,
            "chunk_id": chunk.id,
            "curriculum_code": source.curriculum_code,
            "message": "Resource approved and successfully indexed into catalog & RAG chunk store."
        }
