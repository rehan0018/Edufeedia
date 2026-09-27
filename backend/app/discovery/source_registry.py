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
        creator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decoupled source evaluation separating:
        1. Distribution platform authority
        2. Content creator / educator authority
        Returns authority tier, calculated baseline authority score, and verification flags.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

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
        creator_key = (creator_name or "").strip().lower()
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
        elif platform_meta["tier"] in ["TIER_A", "TIER_B"]:
            # Platform itself is an institutional authority (NCERT, PhET, OpenStax)
            tier = platform_meta["tier"]
            score = float(platform_meta["score"])
            is_verified = platform_meta["is_verified"]
            is_official = platform_meta["is_official"]
            reason = f"Institutional authority platform: {platform_meta['name']} ({tier})"
        else:
            # Platform is general distribution (e.g. YouTube) without a recognized vetted creator
            tier = "TIER_D" if platform_meta.get("is_verified") else "TIER_E"
            score = 0.50 if tier == "TIER_D" else 0.00
            is_verified = False
            is_official = False
            reason = "General creator on distribution platform (Pending human/automated review)"

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
            "embed_allowed": platform_meta.get("embed_allowed", True),
            "reason": reason
        }

    @classmethod
    def get_tier_rank(cls, tier: str) -> int:
        tiers = ["TIER_A", "TIER_B", "TIER_C", "TIER_D", "TIER_E"]
        return tiers.index(tier) if tier in tiers else 99

    @classmethod
    def list_sources(cls) -> List[Dict[str, Any]]:
        """
        Returns structured list of registered platforms and vetted creators.
        """
        results = []
        for domain, meta in cls.PLATFORM_REGISTRY.items():
            results.append({
                "type": "platform",
                "identifier": domain,
                "name": meta["name"],
                "authority_tier": meta["tier"],
                "authority_score": meta["score"],
                "is_official": meta.get("is_official", False),
                "is_verified": meta.get("is_verified", False)
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
                "subject": c_meta.get("subject", "General STEM")
            })
        return results

