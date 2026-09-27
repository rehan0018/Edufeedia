"""
Federated Candidate Builder.
Gathers educational candidates from internal Edufeedia catalog (including Socratic animations),
official NCERT textbooks, PhET interactive simulations, and vetted YouTube channels.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import ContentItem
from app.discovery.ncert_search import NCERTSearchAdapter
from app.discovery.oer_search import OERSearchAdapter
from app.discovery.youtube_search import YouTubeDiscoveryAdapter
from app.schemas.schemas import InterpretedIntent

class CandidateBuilder:
    """
    Federates multiple discovery streams into an unranked candidate pool (30-50 candidates).
    """

    @classmethod
    def build_candidate_pool(
        cls,
        db: Session,
        intent: InterpretedIntent,
        max_total_candidates: int = 40
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        topic_lower = intent.topic.lower()

        # 1. Internal Edufeedia Catalog (includes Socratic animated lessons)
        try:
            db_items = db.query(ContentItem).filter(
                ContentItem.is_approved == True
            ).all()

            for item in db_items:
                # Match topic or subject
                title_lower = (item.title or "").lower()
                topic_match = (
                    intent.topic.lower() in (item.topic or "").lower() or
                    (item.topic or "").lower() in intent.topic.lower() or
                    any(term.lower() in title_lower for term in intent.expanded_terms[:3])
                )
                grade_match = abs((item.grade_level or 8) - intent.grade_level) <= 2

                if topic_match and grade_match:
                    candidates.append({
                        "id": item.id,
                        "title": item.title,
                        "description": item.description or f"Edufeedia interactive curriculum module for {item.topic}",
                        "source_url": item.source_url,
                        "embed_url": item.embed_code or item.source_url,
                        "source_name": "Edufeedia Originals" if item.is_cartoon else item.source_platform,
                        "source_platform": item.source_platform,
                        "creator_name": "Edufeedia Curriculum Studio" if item.is_cartoon else (item.creator_name or "Edufeedia Certified Educator"),
                        "creator_id": "edufeedia_studio",
                        "resource_type": "animation" if item.is_cartoon else (item.type or "video"),
                        "subject": item.subject or intent.subject,
                        "topic": item.topic or intent.topic,
                        "grade_level": item.grade_level or intent.grade_level,
                        "board": item.board or intent.board,
                        "language": item.language or intent.language,
                        "duration_minutes": item.duration_minutes or 6,
                        "view_count": item.view_count or 15000,
                        "is_cartoon": item.is_cartoon or False,
                        "transcript_text": item.transcript_text or "",
                        "provenance_metadata": item.provenance_metadata or {},
                        "origin": "catalog"
                    })
        except Exception:
            pass

        # 2. NCERT Official Chapter Readings
        ncert_results = NCERTSearchAdapter.search(
            topic=intent.topic,
            grade_level=intent.grade_level,
            board=intent.board,
            subject=intent.subject,
            db=db
        )
        for nr in ncert_results:
            candidates.append({
                "id": nr["id"],
                "title": nr["title"],
                "description": nr["description"],
                "source_url": nr["source_url"],
                "embed_url": None,
                "source_name": "NCERT Official",
                "source_platform": "NCERT",
                "creator_name": "National Council of Educational Research and Training",
                "creator_id": "ncert_nic_in",
                "resource_type": "reading",
                "subject": nr["subject"],
                "topic": nr["topic"],
                "grade_level": nr["grade_level"],
                "board": nr["board"],
                "language": "en",
                "duration_minutes": nr.get("read_time_minutes", 12),
                "view_count": 250000,
                "is_cartoon": False,
                "transcript_text": nr.get("excerpt", ""),
                "provenance_metadata": {
                    "chapter": nr.get("chapter"),
                    "learning_outcomes": nr.get("learning_outcomes", [])
                },
                "origin": "ncert"
            })

        # 3. PhET & Khan Academy Interactive Simulations
        oer_results = OERSearchAdapter.search(
            topic=intent.topic,
            grade_level=intent.grade_level,
            preferred_format=intent.format_preference,
            db=db
        )
        for or_item in oer_results:
            candidates.append({
                "id": or_item["id"],
                "title": or_item["title"],
                "description": or_item["description"],
                "source_url": or_item["source_url"],
                "embed_url": or_item.get("embed_url"),
                "source_name": or_item["source_name"],
                "source_platform": or_item["source_platform"],
                "creator_name": or_item["source_name"],
                "creator_id": or_item["source_platform"].lower(),
                "resource_type": or_item["resource_type"],
                "subject": or_item["subject"],
                "topic": or_item["topic"],
                "grade_level": or_item["grade_level"],
                "board": or_item["board"],
                "language": "en",
                "duration_minutes": or_item.get("duration_minutes", 10),
                "view_count": 650000,
                "is_cartoon": False,
                "transcript_text": or_item["description"],
                "provenance_metadata": {"license": or_item.get("license")},
                "origin": "oer"
            })

        # 4. YouTube Educational Videos from Vetted Creators
        yt_results = YouTubeDiscoveryAdapter.search_candidates(
            query=intent.topic,
            topic=intent.topic,
            grade_level=intent.grade_level,
            language=intent.language,
            max_results=8
        )
        for yr in yt_results:
            candidates.append({
                "id": yr["id"],
                "title": yr["title"],
                "description": yr["description"],
                "source_url": yr["source_url"],
                "embed_url": yr.get("embed_url"),
                "source_name": yr["channel_title"],
                "source_platform": "YouTube",
                "creator_name": yr["creator_name"],
                "creator_id": yr["creator_id"],
                "resource_type": "video",
                "subject": yr.get("subject", intent.subject),
                "topic": yr.get("topic", intent.topic),
                "grade_level": yr.get("grade_level", intent.grade_level),
                "board": yr.get("board", intent.board),
                "language": yr.get("language", "en"),
                "duration_minutes": yr.get("duration_minutes", 8),
                "view_count": yr.get("view_count", 100000),
                "is_cartoon": False,
                "transcript_text": yr.get("transcript_summary", ""),
                "provenance_metadata": {"channel_id": yr.get("creator_id")},
                "origin": "youtube"
            })

        return candidates[:max_total_candidates]
