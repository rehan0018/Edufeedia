import re
import requests
from typing import Dict, Any, Optional
from app.ingestion.adapters.base import ContentSourceAdapter

class YouTubeAdapter(ContentSourceAdapter):
    """
    YouTube Safe Educational Adapter using official oEmbed API and privacy-enhanced embeds.
    """

    OEMBED_ENDPOINT = "https://www.youtube.com/oembed"

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        clean = url.lower()
        return "youtube.com" in clean or "youtu.be" in clean

    def _extract_video_id(self, url: str) -> Optional[str]:
        match = re.search(r'(?:v=|\/embed\/|youtu\.be\/|\/v\/)([a-zA-Z0-9_\-]{11})', url)
        if match:
            return match.group(1)
        return None

    def fetch_content_metadata(self, url: str) -> Dict[str, Any]:
        video_id = self._extract_video_id(url)
        if not video_id:
            return {
                "success": False,
                "error": "INVALID_YOUTUBE_URL",
                "message": "Could not extract standard 11-character YouTube video ID."
            }

        # Safe YouTube-nocookie embed with modest branding and related video suppression
        embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1"
        embed_code = f'<iframe width="560" height="315" src="{embed_url}" title="Safe Educational Lesson" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'

        # Attempt to fetch oEmbed metadata (Title, Author, Thumbnail)
        title = f"Educational Video ({video_id})"
        author_name = "Educational Channel"
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        try:
            resp = requests.get(
                self.OEMBED_ENDPOINT,
                params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
                timeout=4.0
            )
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", title)
                author_name = data.get("author_name", author_name)
                thumbnail_url = data.get("thumbnail_url", thumbnail_url)
        except Exception:
            # Fallback to standard derived metadata if offline/network timeout
            pass

        return {
            "success": True,
            "platform": "youtube",
            "video_id": video_id,
            "title": title,
            "author": author_name,
            "thumbnail_url": thumbnail_url,
            "embed_code": embed_code,
            "content_type": "video",
            "is_child_safe_embed": True
        }
