from typing import List, Optional, Dict, Any
from app.ingestion.adapters.base import ContentSourceAdapter
from app.ingestion.adapters.youtube import YouTubeAdapter
from app.ingestion.adapters.oer_adapter import OERContentAdapter

class ContentFetcherFactory:
    """
    Factory for dispatching URLs to dedicated educational content adapters.
    """

    _adapters: List[ContentSourceAdapter] = [
        YouTubeAdapter(),
        OERContentAdapter()
    ]

    @classmethod
    def get_adapter(cls, url: str) -> Optional[ContentSourceAdapter]:
        for adapter in cls._adapters:
            if adapter.can_handle(url):
                return adapter
        return None

    @classmethod
    def fetch(cls, url: str) -> Dict[str, Any]:
        adapter = cls.get_adapter(url)
        if not adapter:
            return {
                "success": False,
                "error": "UNSUPPORTED_ADAPTER",
                "message": f"No dedicated adapter found for URL: {url}"
            }
        return adapter.fetch_content_metadata(url)
