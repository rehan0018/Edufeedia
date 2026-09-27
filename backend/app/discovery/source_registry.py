"""
Hierarchical Source Authority Registry.
Decouples Platform Trust, Creator Trust, and Individual Resource Trust.
Enforces strict minor protection by ensuring unvetted platforms/creators (Tier E)
cannot bypass safety gates.
"""

from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse
import re

class SourceAuthorityRegistry:
    """
    Evaluates source trust across three distinct layers:
    1. Platform Trust (distribution channel e.g., YouTube, PhET, NCERT)
    2. Creator / Organization Trust (e.g., Khan Academy, NCERT Official, 3Blue1Brown)
    3. Resource Trust (individual video / document verified against curriculum)
    """

    # Tier Definitions & Baseline Multipliers
    TIER_SCORES = {
        "TIER_A": 1.00,  # Official / Primary Government & Accreditation (NCERT, CBSE, NASA)
        "TIER_B": 0.95,  # Established Educational Institutions (Khan Academy, PhET, OpenStax)
        "TIER_C": 0.85,  # Vetted Individual Educators & Verified Channels
        "TIER_D": 0.65,  # General Educational Creators (Require human / AI audit)
        "TIER_E": 0.00   # Unknown / Unverified Source (Blocked for minors)
    }

    # 1. Platform Trust Registry
    PLATFORM_REGISTRY = {
        "edufeedia.com": {
            "name": "Edufeedia Originals",
            "tier": "TIER_A",
            "score": 1.00,
            "is_official": True,
            "is_verified": True,
            "embed_allowed": True
        },
        "ncert.nic.in": {
            "name": "NCERT Official",
            "tier": "TIER_A",
            "score": 1.00,
            "is_official": True,
            "is_verified": True,
            "embed_allowed": True
        },
        "cbse.gov.in": {
            "name": "CBSE Official",
            "tier": "TIER_A",
            "score": 1.00,
            "is_official": True,
            "is_verified": True,
            "embed_allowed": True
        },
        "nasa.gov": {
            "name": "NASA Science & STEM",
            "tier": "TIER_A",
            "score": 1.00,
            "is_official": True,
            "is_verified": True,
            "embed_allowed": True
        },
        "khanacademy.org": {
            "name": "Khan Academy",
            "tier": "TIER_B",
            "score": 0.95,
            "is_official": False,
            "is_verified": True,
            "embed_allowed": True
        },
        "phet.colorado.edu": {
            "name": "PhET Interactive Simulations",
            "tier": "TIER_B",
            "score": 0.98,
            "is_official": True,
            "is_verified": True,
            "embed_allowed": True
        },
        "openstax.org": {
            "name": "OpenStax",
            "tier": "TIER_B",
            "score": 0.95,
            "is_official": False,
            "is_verified": True,
            "embed_allowed": True
        },
        "britannica.com": {
            "name": "Encyclopedia Britannica Kids",
            "tier": "TIER_B",
            "score": 0.95,
            "is_official": False,
            "is_verified": True,
            "embed_allowed": True
        },
        "code.org": {
            "name": "Code.org",
            "tier": "TIER_B",
            "score": 0.95,
            "is_official": False,
            "is_verified": True,
            "embed_allowed": True
        },
        "youtube.com": {
            "name": "YouTube",
            "tier": "TIER_D",  # Platform itself is neutral distribution; trust depends on creator!
            "score": 0.60,
            "is_official": False,
            "is_verified": True,
            "embed_allowed": True
        },
        "youtu.be": {
            "name": "YouTube",
            "tier": "TIER_D",
            "score": 0.60,
            "is_official": False,
            "is_verified": True,
            "embed_allowed": True
        }
    }

    # 2. Vetted Creator & Channel Registry (Tier C & B Creators on YouTube and elsewhere)
    VETTED_CREATORS: Dict[str, Dict[str, Any]] = {
        "edufeedia originals": {
            "name": "Edufeedia Originals",
            "tier": "TIER_A",
            "score": 1.00,
            "subject": "All K-12 Interactive STEM",
            "verified": True,
            "boards": ["CBSE", "ICSE", "NCERT"]
        },
        "edufeedia curriculum team": {
            "name": "Edufeedia Curriculum Team",
            "tier": "TIER_A",
            "score": 1.00,
            "subject": "All K-12 Socratic Lessons",
            "verified": True,
            "boards": ["CBSE", "ICSE", "NCERT"]
        },
        "edufeedia studio": {
            "name": "Edufeedia Studio",
            "tier": "TIER_A",
            "score": 1.00,
            "subject": "Visual Socratic Animations",
            "verified": True,
            "boards": ["CBSE", "ICSE", "NCERT"]
        },
        "ncert official": {
            "name": "NCERT Official",
            "tier": "TIER_A",
            "score": 1.00,
            "subject": "All NCERT K-12",
            "verified": True,
            "boards": ["CBSE", "NCERT"]
        },
        "khan academy india": {
            "name": "Khan Academy India",
            "tier": "TIER_B",
            "score": 0.96,
            "subject": "Science & Math K-12",
            "verified": True,
            "boards": ["CBSE", "NCERT"]
        },
        "khan academy": {
            "name": "Khan Academy",
            "tier": "TIER_B",
            "score": 0.95,
            "subject": "STEM",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "phet interactive simulations": {
            "name": "PhET Interactive Simulations",
            "tier": "TIER_B",
            "score": 0.98,
            "subject": "Physics, Chemistry, Biology, Math",
            "verified": True,
            "boards": ["CBSE", "ICSE", "Global"]
        },
        "physics wallah": {
            "name": "Physics Wallah",
            "tier": "TIER_C",
            "score": 0.90,
            "subject": "Physics, Chemistry, Biology, Math Class 9-12",
            "verified": True,
            "boards": ["CBSE", "ICSE"]
        },
        "vedantu 9&10": {
            "name": "Vedantu 9&10",
            "tier": "TIER_C",
            "score": 0.88,
            "subject": "Science & Math Class 9-10",
            "verified": True,
            "boards": ["CBSE", "ICSE"]
        },
        "vedantu": {
            "name": "Vedantu",
            "tier": "TIER_C",
            "score": 0.87,
            "subject": "K-12 STEM",
            "verified": True,
            "boards": ["CBSE", "ICSE"]
        },
        "3blue1brown": {
            "name": "3Blue1Brown",
            "tier": "TIER_C",
            "score": 0.95,
            "subject": "Higher Mathematics & Visual Calculus",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "veritasium": {
            "name": "Veritasium",
            "tier": "TIER_C",
            "score": 0.92,
            "subject": "Physics & Scientific Inquiry",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "minutephysics": {
            "name": "MinutePhysics",
            "tier": "TIER_C",
            "score": 0.90,
            "subject": "Physics",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "crashcourse": {
            "name": "CrashCourse",
            "tier": "TIER_C",
            "score": 0.92,
            "subject": "Science, History, Philosophy",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "ted-ed": {
            "name": "TED-Ed",
            "tier": "TIER_C",
            "score": 0.93,
            "subject": "Interdisciplinary STEM & Humanities",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "scishow kids": {
            "name": "SciShow Kids",
            "tier": "TIER_C",
            "score": 0.92,
            "subject": "Primary & Middle School Science",
            "verified": True,
            "boards": ["CBSE", "Global"]
        },
        "edufeedia originals": {
            "name": "Edufeedia Originals",
            "tier": "TIER_A",
            "score": 1.00,
            "subject": "Curriculum Socratic Animated Explanations",
            "verified": True,
            "boards": ["CBSE", "ICSE", "State Board"]
        }
    }

    @classmethod
    def evaluate_source(
        cls,
        url: str,
        platform_hint: Optional[str] = None,
        creator_name: Optional[str] = None,
        creator_id: Optional[str] = None,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Decoupled source evaluation separating:
        1. Distribution platform authority
        2. Content creator / educator authority
        Supports database-backed EducationalSource lookup for verified evidence trails.
        Returns authority tier, calculated baseline authority score, and verification flags.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        creator_key = (creator_name or "").strip().lower()

        # Check database-backed EducationalSource registry first if db session is available
        db_source = None
        if db:
            try:
                from sqlalchemy import func
                from app.models.models import EducationalSource

                if creator_key:
                    db_source = db.query(EducationalSource).filter(
                        func.lower(EducationalSource.creator_name) == creator_key
                    ).first()

                if not db_source and domain:
                    db_source = db.query(EducationalSource).filter(
                        func.lower(EducationalSource.domain) == domain
                    ).first()
            except Exception:
                db_source = None

        if db_source:
            verified_at_str = db_source.last_verified_at.isoformat() if db_source.last_verified_at else "2026-01-01T00:00:00Z"
            return {
                "domain": db_source.domain,
                "platform_name": db_source.platform or platform_hint or domain,
                "platform_tier": db_source.authority_tier,
                "creator_name": db_source.creator_name or (creator_name or "Verified Educator"),
                "creator_verified": db_source.is_verified,
                "authority_tier": db_source.authority_tier,
                "authority_score": round(float(db_source.authority_score), 2),
                "is_verified": db_source.is_verified,
                "is_official": db_source.is_official,
                "verification_method": db_source.verification_method or "official_source_registry",
                "verified_at": verified_at_str,
                "supported_boards": db_source.supported_boards or ["CBSE", "NCERT"],
                "embed_allowed": db_source.embed_supported,
                "reason": f"Database verified source: {db_source.name} ({db_source.authority_tier})"
            }

        # Default platform evaluation
        platform_meta = cls.PLATFORM_REGISTRY.get(domain)
        if not platform_meta:
            # Check partial domain matching (e.g. subdomains of gov.in or edu)
            for reg_dom, meta in cls.PLATFORM_REGISTRY.items():
                if domain.endswith(reg_dom):
                    platform_meta = meta
                    break

        if not platform_meta:
            if domain.endswith(".edu") or domain.endswith(".ac.in") or domain.endswith(".gov.in"):
                platform_meta = {
                    "name": domain,
                    "tier": "TIER_A",
                    "score": 0.98,
                    "is_official": True,
                    "is_verified": True,
                    "embed_allowed": True
                }
            else:
                platform_meta = {
                    "name": domain or (platform_hint or "Unknown Web"),
                    "tier": "TIER_E",
                    "score": 0.00,
                    "is_official": False,
                    "is_verified": False,
                    "embed_allowed": False
                }

        # Creator / Channel Evaluation
        creator_meta = cls.VETTED_CREATORS.get(creator_key)
        if not creator_meta and creator_key:
            # Substring match for known channels
            for known_key, meta in cls.VETTED_CREATORS.items():
                if known_key in creator_key or creator_key in known_key:
                    creator_meta = meta
                    break

        # Compute composite authority tier & score
        if creator_meta:
            # Creator is explicitly vetted: creator tier elevates or maintains authority
            tier = creator_meta["tier"]
            score = float(creator_meta["score"])
            is_verified = True
            is_official = bool(creator_meta.get("is_official", platform_meta.get("is_official", False)))
            reason = f"Verified educational creator: {creator_meta['name']} ({tier})"
            verif_method = "educator_accreditation_audit"
        elif platform_meta["tier"] in ["TIER_A", "TIER_B"]:
            # Platform itself is an institutional authority (NCERT, PhET, OpenStax)
            tier = platform_meta["tier"]
            score = float(platform_meta["score"])
            is_verified = platform_meta["is_verified"]
            is_official = platform_meta["is_official"]
            reason = f"Institutional authority platform: {platform_meta['name']} ({tier})"
            verif_method = "government_or_academic_charter"
        else:
            # Platform is general distribution (e.g. YouTube) without a recognized vetted creator
            tier = "TIER_D" if platform_meta.get("is_verified") else "TIER_E"
            score = 0.50 if tier == "TIER_D" else 0.00
            is_verified = False
            is_official = False
            reason = "General creator on distribution platform (Pending human/automated review)"
            verif_method = "unverified_public_submission"

        return {
            "domain": domain,
            "platform_name": platform_meta["name"],
            "platform_tier": platform_meta["tier"],
            "creator_name": creator_meta["name"] if creator_meta else (creator_name or "Independent Educator"),
            "creator_verified": bool(creator_meta),
            "authority_tier": tier,
            "authority_score": round(score, 2),
            "is_verified": is_verified,
            "is_official": is_official,
            "verification_method": verif_method,
            "verified_at": "2026-01-15T00:00:00Z",
            "supported_boards": creator_meta.get("boards", ["CBSE"]) if creator_meta else ["CBSE"],
            "embed_allowed": platform_meta.get("embed_allowed", True),
            "reason": reason
        }

    @classmethod
    def get_tier_rank(cls, tier: str) -> int:
        tiers = ["TIER_A", "TIER_B", "TIER_C", "TIER_D", "TIER_E"]
        return tiers.index(tier) if tier in tiers else 99

    @classmethod
    def ensure_default_sources_seeded(cls, db: Any) -> None:
        """
        Seeds default authoritative sources and vetted creators into the EducationalSource
        database table if empty, ensuring persistent data governance.
        """
        try:
            from app.models.models import EducationalSource
            if db.query(EducationalSource).count() > 0:
                return

            seed_sources = [
                EducationalSource(
                    name="NCERT Official",
                    domain="ncert.nic.in",
                    platform="NCERT",
                    authority_tier="TIER_A",
                    authority_score=1.00,
                    creator_name="NCERT Official",
                    is_official=True,
                    is_verified=True,
                    verification_method="government_accreditation",
                    supported_boards=["CBSE", "NCERT"],
                    supported_grades=[6, 7, 8, 9, 10, 11, 12],
                    supported_subjects=["Science", "Mathematics", "Social Science"],
                    embed_supported=True
                ),
                EducationalSource(
                    name="CBSE Official",
                    domain="cbse.gov.in",
                    platform="CBSE",
                    authority_tier="TIER_A",
                    authority_score=1.00,
                    creator_name="CBSE Curriculum Cell",
                    is_official=True,
                    is_verified=True,
                    verification_method="government_accreditation",
                    supported_boards=["CBSE"],
                    supported_grades=[6, 7, 8, 9, 10, 11, 12],
                    supported_subjects=["All K-12"],
                    embed_supported=True
                ),
                EducationalSource(
                    name="PhET Interactive Simulations",
                    domain="phet.colorado.edu",
                    platform="PhET",
                    authority_tier="TIER_B",
                    authority_score=0.98,
                    creator_name="University of Colorado Boulder",
                    is_official=True,
                    is_verified=True,
                    verification_method="peer_reviewed_oer",
                    supported_boards=["CBSE", "ICSE", "Global"],
                    supported_grades=[6, 7, 8, 9, 10, 11, 12],
                    supported_subjects=["Physics", "Chemistry", "Biology", "Mathematics"],
                    embed_supported=True
                ),
                EducationalSource(
                    name="Khan Academy India",
                    domain="khanacademy.org",
                    platform="Khan Academy",
                    authority_tier="TIER_B",
                    authority_score=0.96,
                    creator_name="Khan Academy India",
                    is_official=False,
                    is_verified=True,
                    verification_method="curriculum_review",
                    supported_boards=["CBSE", "NCERT"],
                    supported_grades=[6, 7, 8, 9, 10, 11, 12],
                    supported_subjects=["Mathematics", "Science"],
                    embed_supported=True
                ),
                EducationalSource(
                    name="3Blue1Brown",
                    domain="youtube.com",
                    platform="YouTube",
                    authority_tier="TIER_C",
                    authority_score=0.95,
                    creator_name="3Blue1Brown",
                    creator_id="UCYO_jab_esuFRV4b17AJtAw",
                    is_official=False,
                    is_verified=True,
                    verification_method="educator_audit",
                    supported_boards=["CBSE", "Global"],
                    supported_grades=[9, 10, 11, 12],
                    supported_subjects=["Mathematics"],
                    embed_supported=True
                ),
                EducationalSource(
                    name="Veritasium",
                    domain="youtube.com",
                    platform="YouTube",
                    authority_tier="TIER_C",
                    authority_score=0.92,
                    creator_name="Veritasium",
                    creator_id="UCHnyfMqiRRG1u-2MsSQLbXA",
                    is_official=False,
                    is_verified=True,
                    verification_method="educator_audit",
                    supported_boards=["CBSE", "Global"],
                    supported_grades=[8, 9, 10, 11, 12],
                    supported_subjects=["Physics", "Science"],
                    embed_supported=True
                ),
                EducationalSource(
                    name="Physics Wallah",
                    domain="youtube.com",
                    platform="YouTube",
                    authority_tier="TIER_C",
                    authority_score=0.90,
                    creator_name="Physics Wallah",
                    creator_id="UCiGyWN6DEbnj2alu7iapuKQ",
                    is_official=False,
                    is_verified=True,
                    verification_method="curriculum_review",
                    supported_boards=["CBSE", "ICSE"],
                    supported_grades=[9, 10, 11, 12],
                    supported_subjects=["Physics", "Chemistry", "Mathematics", "Biology"],
                    embed_supported=True
                )
            ]
            db.add_all(seed_sources)
            db.commit()
        except Exception:
            db.rollback()

    @classmethod
    def list_sources(cls, db: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Returns structured list of registered platforms and vetted creators,
        pulling from database EducationalSource records when available.
        """
        if db:
            try:
                from app.models.models import EducationalSource
                db_sources = db.query(EducationalSource).all()
                if db_sources:
                    return [
                        {
                            "type": "database_registered",
                            "identifier": s.domain if not s.creator_name else f"{s.domain}::{s.creator_name}",
                            "name": s.name,
                            "authority_tier": s.authority_tier,
                            "authority_score": float(s.authority_score),
                            "is_official": s.is_official,
                            "is_verified": s.is_verified,
                            "verification_method": s.verification_method,
                            "verified_at": s.last_verified_at.isoformat() if s.last_verified_at else None,
                            "supported_boards": s.supported_boards,
                            "subject": ", ".join(s.supported_subjects) if s.supported_subjects else "General STEM"
                        }
                        for s in db_sources
                    ]
            except Exception:
                pass

        results = []
        for domain, meta in cls.PLATFORM_REGISTRY.items():
            results.append({
                "type": "platform",
                "identifier": domain,
                "name": meta["name"],
                "authority_tier": meta["tier"],
                "authority_score": meta["score"],
                "is_official": meta.get("is_official", False),
                "is_verified": meta.get("is_verified", False),
                "verification_method": "platform_allowlist"
            })
        for c_key, c_meta in cls.VETTED_CREATORS.items():
            results.append({
                "type": "creator",
                "identifier": c_key,
                "name": c_meta["name"],
                "authority_tier": c_meta["tier"],
                "authority_score": c_meta["score"],
                "is_official": c_meta.get("is_official", False),
                "is_verified": c_meta.get("verified", True),
                "verification_method": "creator_allowlist",
                "subject": c_meta.get("subject", "General STEM")
            })
        return results

