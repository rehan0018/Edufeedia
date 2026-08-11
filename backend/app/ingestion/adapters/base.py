from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ContentSourceAdapter(ABC):
    """
    Abstract Base Adapter for Educational Content Providers.
    """

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Returns True if this adapter is capable of handling the specified URL."""
        pass

    @abstractmethod
    def fetch_content_metadata(self, url: str) -> Dict[str, Any]:
        """
        Fetches live metadata, title, author, transcript/description,
        and safe embed code for the specified educational URL.
        """
        pass
