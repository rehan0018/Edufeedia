import re
import urllib.request
import logging
from typing import Dict, Any, List, Optional
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

class EducationalHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.extracted_chunks: List[str] = []
        self.headings: List[Dict[str, str]] = []
        self._current_tag = None
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "nav", "footer", "header", "aside", "noscript", "form"}

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag.lower()
        if self._current_tag in self._skip_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
        self._current_tag = None

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        if self._current_tag in {"h1", "h2", "h3", "h4"}:
            self.headings.append({"level": self._current_tag, "title": text})
            self.extracted_chunks.append(f"\n### {text}\n")
        elif self._current_tag in {"p", "li", "td", "th", "div", "span"} or self._current_tag is None:
            self.extracted_chunks.append(text)

class HTMLExtractor:
    """
    Extracts clean pedagogical article text and section outlines from Web / OER pages.
    """

    @classmethod
    def extract_from_html(cls, html_content: str, source_url: Optional[str] = None) -> Dict[str, Any]:
        parser = EducationalHTMLParser()
        try:
            parser.feed(html_content)
        except Exception as e:
            logger.warning("[HTMLExtractor Error]: %s", e)

        raw_text = " ".join(parser.extracted_chunks)
        clean_text = re.sub(r"\s+", " ", raw_text).strip()

        return {
            "success": len(clean_text) > 0,
            "extracted_text": clean_text,
            "headings": parser.headings,
            "char_count": len(clean_text)
        }

    @classmethod
    def fetch_and_extract(cls, url: str) -> Dict[str, Any]:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Edufeedia-Educational-Ingestion-Bot/2.0 (K-12 Verification)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8", errors="ignore")
                return cls.extract_from_html(content, source_url=url)
        except Exception as e:
            logger.warning("[HTMLExtractor Fetch Failure]: %s: %s", url, e)
            return {
                "success": False,
                "extracted_text": "",
                "error": str(e)
            }
