import re
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional

# Curated Trusted Educational Whitelist
TRUSTED_EDUCATIONAL_DOMAINS = {
    "youtube.com": {
        "platform": "YouTube Safe EDU",
        "embed_allowed": True,
        "requires_embed_wrapper": True,
        "is_official_partner": False,
        "default_safety_score": 95
    },
    "youtu.be": {
        "platform": "YouTube Safe EDU",
        "embed_allowed": True,
        "requires_embed_wrapper": True,
        "is_official_partner": False,
        "default_safety_score": 95
    },
    "khanacademy.org": {
        "platform": "Khan Academy",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "is_official_partner": True,
        "default_safety_score": 100
    },
    "phet.colorado.edu": {
        "platform": "PhET Interactive Simulations",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "is_official_partner": True,
        "default_safety_score": 100
    },
    "openstax.org": {
        "platform": "OpenStax",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "is_official_partner": True,
        "default_safety_score": 100
    },
    "ncert.nic.in": {
        "platform": "NCERT Official",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "is_official_partner": True,
        "default_safety_score": 100
    },
    "physicsclassroom.com": {
        "platform": "Physics Classroom",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "is_official_partner": False,
        "default_safety_score": 98
    },
    "britannica.com": {
        "platform": "Encyclopedia Britannica Kids",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "is_official_partner": False,
        "default_safety_score": 98
    },
    "nasa.gov": {
        "platform": "NASA Educational Resources",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "is_official_partner": True,
        "default_safety_score": 100
    },
    "code.org": {
        "platform": "Code.org",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "is_official_partner": True,
        "default_safety_score": 100
    }
}

BLOCKED_OR_HIGH_RISK_PATTERNS = [
    r'tiktok\.com',
    r'instagram\.com',
    r'snapchat\.com',
    r'reddit\.com',
    r'twitter\.com',
    r'x\.com',
    r'twitch\.tv',
    r'discord\.gg',
    r'adclick',
    r'affiliate',
    r'gambling',
    r'betting'
]

class SourceVerifier:
    """
    Verifies educational content sources for copyright safety, domain trust,
    and child-safe embedding compliance.
    """

    @classmethod
    def verify_url(cls, url: str) -> Dict[str, Any]:
        if not url or not url.strip():
            return {
                "is_verified": False,
                "domain": None,
                "platform": "Unknown",
                "is_trusted_domain": False,
                "embed_safe": False,
                "embed_code": None,
                "reason": "URL cannot be empty."
            }

        url = url.strip()
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # 1. Check for blocked/entertainment social media sources
        for pattern in BLOCKED_OR_HIGH_RISK_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return {
                    "is_verified": False,
                    "domain": netloc,
                    "platform": "Blocked Entertainment / Social Platform",
                    "is_trusted_domain": False,
                    "embed_safe": False,
                    "embed_code": None,
                    "reason": "Source matches blocked social media or high-distraction domain."
                }

        # 2. Check Whitelist
        trusted_info = None
        matched_domain = None
        for d, info in TRUSTED_EDUCATIONAL_DOMAINS.items():
            if netloc == d or netloc.endswith(f".{d}"):
                trusted_info = info
                matched_domain = d
                break

        if not trusted_info:
            return {
                "is_verified": False,
                "is_trusted": False,
                "domain": netloc,
                "platform": "Unverified External Source",
                "is_trusted_domain": False,
                "embed_safe": False,
                "embed_code": None,
                "reason": f"Domain '{netloc}' is not in Edufeedia's curated educational whitelist. Requires administrative manual audit."
            }

        # 3. Generate Safe Embed Code if applicable
        embed_code = None
        if "youtube" in matched_domain or "youtu.be" in matched_domain:
            video_id = cls._extract_youtube_id(url)
            if video_id:
                # Use YouTube-nocookie with restricted parameters for under-18 safety
                embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1"
                embed_code = f'<iframe width="560" height="315" src="{embed_url}" title="Safe Educational Lesson" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'

        return {
            "is_verified": True,
            "is_trusted": True,
            "domain": netloc,
            "platform": trusted_info["platform"],
            "is_trusted_domain": True,
            "embed_safe": trusted_info["embed_allowed"],
            "embed_code": embed_code,
            "default_safety_score": trusted_info["default_safety_score"],
            "is_official_partner": trusted_info["is_official_partner"],
            "reason": f"Verified trusted educational source via {trusted_info['platform']}."
        }

    @staticmethod
    def _extract_youtube_id(url: str) -> Optional[str]:
        # Formats: youtube.com/watch?v=XYZ, youtu.be/XYZ, youtube.com/embed/XYZ
        match = re.search(r'(?:v=|\/embed\/|youtu\.be\/|\/v\/)([a-zA-Z0-9_\-]{11})', url)
        if match:
            return match.group(1)
        return None
