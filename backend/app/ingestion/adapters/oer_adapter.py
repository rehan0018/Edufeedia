import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from app.ingestion.adapters.base import ContentSourceAdapter

class OERContentAdapter(ContentSourceAdapter):
    """
    Open Educational Resources (OER) Content Adapter:
    Supports Khan Academy, PhET Interactive Simulations, OpenStax, and NCERT.
    """

    SUPPORTED_OER_DOMAINS = ["khanacademy.org", "phet.colorado.edu", "openstax.org", "ncert.nic.in", "code.org", "nasa.gov"]

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        parsed = urlparse(url.lower())
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return any(netloc == domain or netloc.endswith(f".{domain}") for domain in self.SUPPORTED_OER_DOMAINS)

    def fetch_content_metadata(self, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        path_segments = [s for s in parsed.path.strip("/").split("/") if s]

        # Determine Platform & Derive Structured Metadata from Canonical URL Hierarchy
        platform = "oer"
        embed_code = None
        content_type = "article"

        if "khanacademy.org" in netloc:
            platform = "khan_academy"
            topic_slug = path_segments[-1] if path_segments else "lesson"
            title = topic_slug.replace("-", " ").title()
            content_type = "interactive_course"
        elif "phet.colorado.edu" in netloc:
            platform = "phet"
            sim_slug = path_segments[-1] if path_segments else "simulation"
            title = sim_slug.replace("-", " ").title()
            content_type = "interactive_sim"
            embed_code = f'<iframe src="{url}" width="800" height="600" allowfullscreen title="{title}"></iframe>'
        elif "openstax.org" in netloc:
            platform = "openstax"
            book_slug = path_segments[-1] if path_segments else "textbook"
            title = book_slug.replace("-", " ").title()
            content_type = "textbook_chapter"
        elif "ncert.nic.in" in netloc:
            platform = "ncert"
            title = "NCERT Official Curriculum Unit"
            content_type = "curriculum_text"
        else:
            platform = netloc.split(".")[0]
            title = "Open Educational Resource"

        return {
            "success": True,
            "platform": platform,
            "title": title,
            "source_domain": netloc,
            "content_type": content_type,
            "embed_code": embed_code,
            "is_official_oer": True
        }
