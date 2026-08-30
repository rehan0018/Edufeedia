import hashlib
import datetime
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.models import IngestedSource, ContentItem, CurriculumChunk
from app.ingestion.source_verifier import SourceVerifier
from app.ingestion.metadata_extractor import MetadataExtractor
from app.ingestion.extractors.pdf_extractor import PDFExtractor
from app.ingestion.extractors.html_extractor import HTMLExtractor
from app.ingestion.extractors.youtube_extractor import YouTubeExtractor
from app.ingestion.chunker import SemanticChunker
from app.safety.engine import SafetyEngine
from app.embeddings.embedder import embed_content

logger = logging.getLogger(__name__)

class IngestionStage:
    DISCOVERED = "DISCOVERED"
    FETCHING = "FETCHING"
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    CURRICULUM_MAPPED = "CURRICULUM_MAPPED"
    SAFETY_CHECKED = "SAFETY_CHECKED"
    CHUNKED = "CHUNKED"
    EMBEDDED = "EMBEDDED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class IngestionStateMachine:
    """
    Observable, recoverable 11-stage educational content ingestion state machine.
    Tracks every stage transition, SHA-256 idempotency, retry count, and error provenance.
    """

    PIPELINE_VERSION = "2.0"

    @classmethod
    def run_pipeline(
        cls,
        db: Session,
        url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        raw_text: Optional[str] = None,
        submitted_by: Optional[str] = None,
        board: str = "CBSE",
        grade_level: int = 10
    ) -> Dict[str, Any]:
        url_hash = hashlib.sha256(url.strip().lower().encode('utf-8')).hexdigest()

        # Idempotency check: find existing record
        source = db.query(IngestedSource).filter(IngestedSource.url_hash == url_hash).first()
        if not source:
            source = IngestedSource(
                source_url=url,
                url_hash=url_hash,
                source_platform="unknown",
                title=title or "Discovered Resource",
                description=description,
                raw_text=raw_text,
                board=board,
                grade_level=grade_level,
                status=IngestionStage.DISCOVERED,
                retry_count=0,
                pipeline_version=cls.PIPELINE_VERSION,
                submitted_by=submitted_by
            )
            db.add(source)
            db.commit()
            db.refresh(source)

        try:
            # Stage 1: FETCHING & SOURCE VERIFICATION
            cls._transition(db, source, IngestionStage.FETCHING)
            verification = SourceVerifier.verify_url(url)
            if not verification["is_trusted"]:
                return cls._fail(db, source, "UNTRUSTED_DOMAIN", verification.get("reason", "Source domain is not whitelisted for minors."))
            source.source_platform = verification["platform"]

            # Stage 2: EXTRACTED
            cls._transition(db, source, IngestionStage.EXTRACTED)
            extracted_text = raw_text or ""
            extracted_title = title or source.title
            extracted_desc = description or source.description or ""

            if verification["platform"] == "youtube":
                yt_meta = YouTubeExtractor.extract_video_metadata(url)
                if yt_meta["success"]:
                    extracted_title = title or yt_meta["title"]
                    extracted_text = yt_meta["transcript"]
            elif url.lower().endswith(".pdf"):
                pass
            elif not extracted_text:
                html_res = HTMLExtractor.fetch_and_extract(url)
                if html_res["success"]:
                    extracted_text = html_res["extracted_text"]

            if not extracted_text:
                extracted_text = f"{extracted_title}. {extracted_desc}"

            source.title = extracted_title
            source.raw_text = extracted_text
            source.description = extracted_desc

            # Stage 3: NORMALIZED
            cls._transition(db, source, IngestionStage.NORMALIZED)
            normalized_text = SemanticChunker.normalize_text(extracted_text)
            source.raw_text = normalized_text

            # Stage 4: CURRICULUM_MAPPED
            cls._transition(db, source, IngestionStage.CURRICULUM_MAPPED)
            meta = MetadataExtractor.extract_metadata(
                title=source.title,
                description=source.description,
                raw_text=normalized_text
            )
            source.subject = meta["subject"]
            source.topic = meta["topic"]
            source.grade_level = meta["estimated_grade"]
            source.curriculum_code = meta.get("curriculum_code")
            source.edu_score = meta["edu_score"]

            # Stage 5: SAFETY_CHECKED
            cls._transition(db, source, IngestionStage.SAFETY_CHECKED)
            safety_audit = SafetyEngine.audit_content(
                f"{source.title}. {source.description or ''}. {normalized_text[:400]}",
                target_age=source.grade_level + 5
            )
            source.safety_audit = safety_audit
            if not safety_audit["is_safe"]:
                return cls._fail(db, source, "SAFETY_VIOLATION", f"Content failed safety filter: {safety_audit['explanation']}")

            # Stage 6: CHUNKED
            cls._transition(db, source, IngestionStage.CHUNKED)
            chunks = SemanticChunker.chunk_text(
                text=normalized_text,
                subject=source.subject,
                topic=source.topic,
                chapter=source.topic,
                default_section="Core Concept & Verified Syllabus"
            )

            # Stage 7: EMBEDDED
            cls._transition(db, source, IngestionStage.EMBEDDED)
            source_embedding = embed_content(
                title=source.title,
                description=source.description or "",
                subject=source.subject,
                topic=source.topic,
                tags=[source.subject, source.topic, source.board]
            )

            # Stage 8: PENDING_REVIEW vs AUTO-APPROVAL
            is_auto_approved = verification.get("is_official_partner", False) and safety_audit["safety_score"] >= 95
            if is_auto_approved:
                cls._transition(db, source, IngestionStage.APPROVED)
                
                # Publish Live ContentItem
                content_item = ContentItem(
                    title=source.title,
                    description=source.description,
                    source_url=source.source_url,
                    source_platform=source.source_platform,
                    embed_code=verification.get("embed_code"),
                    type="video" if source.source_platform == "youtube" else "interactive",
                    board=source.board,
                    grade_level=source.grade_level,
                    subject=source.subject,
                    topic=source.topic,
                    difficulty=meta.get("difficulty", "medium"),
                    duration_minutes=10,
                    safety_score=safety_audit["safety_score"],
                    edu_score=source.edu_score,
                    is_approved=True,
                    embedding=source_embedding
                )
                db.add(content_item)
                db.flush()

                # Publish Curriculum Knowledge Chunks with Provenance
                for c in chunks:
                    chunk_embed = embed_content(c["topic"], c["text"], c["subject"], c["section"])
                    db_chunk = CurriculumChunk(
                        source_id=content_item.id,
                        source_url=source.source_url,
                        source_doc=f"{source.title} ({source.subject} - {source.topic})",
                        board=source.board,
                        grade_level=source.grade_level,
                        subject=c["subject"],
                        topic=c["topic"],
                        chapter=c["chapter"],
                        section=c["section"],
                        chunk_index=c["chunk_index"],
                        curriculum_code=source.curriculum_code,
                        chunk_text=c["text"],
                        embedding=chunk_embed
                    )
                    db.add(db_chunk)

                cls._transition(db, source, IngestionStage.PUBLISHED)
                db.commit()
                return {
                    "success": True,
                    "status": IngestionStage.PUBLISHED,
                    "source_id": source.id,
                    "content_item_id": content_item.id,
                    "chunks_indexed": len(chunks),
                    "message": "Educational resource verified, chunked, and published live."
                }
            else:
                cls._transition(db, source, IngestionStage.PENDING_REVIEW)
                db.commit()
                return {
                    "success": True,
                    "status": IngestionStage.PENDING_REVIEW,
                    "source_id": source.id,
                    "chunks_prepared": len(chunks),
                    "message": "Educational resource staged successfully. Awaiting educator moderation."
                }

        except Exception as e:
            logger.error("[IngestionStateMachine Crash]: %s", e, exc_info=True)
            return cls._fail(db, source, "INTERNAL_PIPELINE_ERROR", str(e))

    @classmethod
    def _transition(cls, db: Session, source: IngestedSource, new_status: str):
        source.status = new_status
        source.last_attempt_at = datetime.datetime.utcnow()
        db.flush()

    @classmethod
    def _fail(cls, db: Session, source: IngestedSource, code: str, msg: str) -> Dict[str, Any]:
        source.status = IngestionStage.FAILED
        source.error_code = code
        source.error_message = msg
        source.retry_count = (source.retry_count or 0) + 1
        source.last_attempt_at = datetime.datetime.utcnow()
        db.commit()
        return {
            "success": False,
            "status": IngestionStage.FAILED,
            "error_code": code,
            "error_message": msg,
            "source_id": source.id
        }
