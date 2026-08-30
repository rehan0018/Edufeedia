import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PDFExtractor:
    """
    Production PDF Educational Document Extractor.
    Extracts text, removes repetitive page headers/footers, and parses section hierarchies.
    """

    @classmethod
    def extract_text(cls, raw_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        extracted_text = ""
        pages = []
        try:
            import io
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(raw_content))
                for page_idx, page in enumerate(reader.pages):
                    p_text = page.extract_text() or ""
                    clean_p = cls._clean_page_boilerplate(p_text, page_idx + 1)
                    pages.append({"page_number": page_idx + 1, "text": clean_p})
                    extracted_text += f"\n\n[Page {page_idx + 1}]\n" + clean_p
            except ImportError:
                decoded = raw_content.decode("latin-1", errors="ignore")
                text_blocks = re.findall(r"BT[\s\S]*?\((.*?)\)[\s\S]*?ET", decoded)
                if text_blocks:
                    extracted_text = " ".join(text_blocks)
                else:
                    clean = re.sub(r"[^\x20-\x7E\n]", " ", decoded)
                    extracted_text = re.sub(r"\s+", " ", clean)[:5000]
                pages.append({"page_number": 1, "text": extracted_text})
        except Exception as e:
            logger.warning("[PDFExtractor Error]: %s", e)
            extracted_text = "PDF content could not be fully parsed."

        sections = cls._detect_sections(extracted_text)
        return {
            "success": len(extracted_text.strip()) > 0,
            "extracted_text": extracted_text.strip(),
            "page_count": max(1, len(pages)),
            "pages": pages,
            "sections": sections
        }

    @classmethod
    def _clean_page_boilerplate(cls, text: str, page_num: int) -> str:
        lines = [l.strip() for l in text.split("\n")]
        cleaned_lines = []
        for line in lines:
            if re.match(r"^(page\s*\d+|\d+\s*/\s*\d+|copyright|all rights reserved|ncert|cbse)\b", line, re.IGNORECASE):
                continue
            if len(line) <= 3 and line.isdigit():
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    @classmethod
    def _detect_sections(cls, text: str) -> List[Dict[str, str]]:
        section_pattern = r"(?:(?:Chapter|Section|Unit)\s*\d+|\d+\.\d+)\s+([A-Z][^\n]{3,60})"
        matches = list(re.finditer(section_pattern, text))
        if not matches:
            return [{"title": "Full Document", "text": text}]
        
        sections = []
        for i, match in enumerate(matches):
            title = match.group(0).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sec_text = text[start:end].strip()
            sections.append({"title": title, "text": sec_text})
        return sections
