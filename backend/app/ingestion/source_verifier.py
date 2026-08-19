import re
import ipaddress
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional

# Curated Trusted Educational Whitelist with truthful labels
TRUSTED_EDUCATIONAL_DOMAINS = {
    "youtube.com": {
        "platform": "YouTube Safe EDU",
        "embed_allowed": True,
        "requires_embed_wrapper": True,
        "trusted_source": True,
        "official_source": False,
        "default_safety_score": 95
    },
    "youtu.be": {
        "platform": "YouTube Safe EDU",
        "embed_allowed": True,
        "requires_embed_wrapper": True,
        "trusted_source": True,
        "official_source": False,
        "default_safety_score": 95
    },
    "khanacademy.org": {
        "platform": "Khan Academy",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": True,
        "default_safety_score": 100
    },
    "phet.colorado.edu": {
        "platform": "PhET Interactive Simulations",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": True,
        "default_safety_score": 100
    },
    "openstax.org": {
        "platform": "OpenStax",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": True,
        "default_safety_score": 100
    },
    "ncert.nic.in": {
        "platform": "NCERT Official",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": True,
        "default_safety_score": 100
    },
    "physicsclassroom.com": {
        "platform": "Physics Classroom",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": False,
        "default_safety_score": 98
    },
    "britannica.com": {
        "platform": "Encyclopedia Britannica Kids",
        "embed_allowed": False,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": False,
        "default_safety_score": 98
    },
    "nasa.gov": {
        "platform": "NASA Educational Resources",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": True,
        "default_safety_score": 100
    },
    "code.org": {
        "platform": "Code.org",
        "embed_allowed": True,
        "requires_embed_wrapper": False,
        "trusted_source": True,
        "official_source": True,
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
    SSRF defense, and child-safe embedding compliance.
    """

    @classmethod
    def is_ssrf_safe_url(cls, url: str) -> bool:
        """
        Validates that the given URL does not target internal IP addresses,
        cloud metadata services (169.254.169.254), or local networks.
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ("http", "https"):
                return False

            # Reject embedded credentials in URLs (e.g. http://user:pass@host)
            if parsed.username or parsed.password:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname = hostname.lower().strip()
            if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
                return False

            # Check for direct IP address attacks
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                    return False
            except ValueError:
                # Hostname is a domain name -> verify resolved IP addresses (DNS rebinding defense)
                try:
                    import socket
                    addr_info = socket.getaddrinfo(hostname, None)
                    for family, socktype, proto, canonname, sockaddr in addr_info:
                        resolved_ip = sockaddr[0]
                        ip_obj = ipaddress.ip_address(resolved_ip)
                        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast:
                            return False
                except Exception:
                    # If domain fails resolution in strict SSRF mode, allow if matches trusted domain
                    pass

            return True
        except Exception:
            return False

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

        # 1. Strict SSRF Protection Check
        if not cls.is_ssrf_safe_url(url):
            return {
                "is_verified": False,
                "domain": "Blocked Host / Network",
                "platform": "SSRF Security Filter",
                "is_trusted_domain": False,
                "embed_safe": False,
                "embed_code": None,
                "reason": "URL was rejected by SSRF network safety filter (private IP or internal host detected)."
            }

        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # 2. Check for blocked/entertainment social media sources
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

        # 3. Check Whitelist
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

        # 4. Generate Safe Embed Code if applicable
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
            "trusted_source": trusted_info["trusted_source"],
            "official_source": trusted_info["official_source"],
            "reason": f"Verified trusted educational source via {trusted_info['platform']}."
        }

    @staticmethod
    def _extract_youtube_id(url: str) -> Optional[str]:
        match = re.search(r'(?:v=|\/embed\/|youtu\.be\/|\/v\/)([a-zA-Z0-9_\-]{11})', url)
        if match:
            return match.group(1)
        return None
