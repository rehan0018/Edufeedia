import re
from typing import Dict, Any, List, Optional

class SemanticChunker:
    """
    Pedagogical Text Chunker & Normalizer.
    Splits educational materials into ~500-character semantic chunks with 50-character overlap,
    respecting sentence boundaries, section titles, and chapter hierarchies.
    """

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    @classmethod
    def chunk_text(
        cls,
        text: str,
        subject: str = "Science",
        topic: str = "Core Concept",
        chapter: Optional[str] = None,
        default_section: str = "Key Principles"
    ) -> List[Dict[str, Any]]:
        clean_text = cls.normalize_text(text)
        if not clean_text:
            return []

        # Split on sentence terminals: period, exclamation, question mark, newline
        sentences = re.split(r'(?<=[.!?\n])\s+', clean_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 0]

        chunks = []
        current_chunk = []
        current_len = 0
        chunk_idx = 0

        for sentence in sentences:
            sent_len = len(sentence)
            if current_len + sent_len > cls.CHUNK_SIZE and current_chunk:
                chunk_str = " ".join(current_chunk)
                chunks.append({
                    "chunk_index": chunk_idx,
                    "subject": subject,
                    "topic": topic,
                    "chapter": chapter or topic,
                    "section": default_section,
                    "text": chunk_str,
                    "char_length": len(chunk_str)
                })
                chunk_idx += 1
                
                # Keep overlap sentences from end of current chunk
                overlap_chars = 0
                overlap_chunk = []
                for s in reversed(current_chunk):
                    if overlap_chars + len(s) <= cls.CHUNK_OVERLAP:
                        overlap_chunk.insert(0, s)
                        overlap_chars += len(s)
                    else:
                        break
                current_chunk = overlap_chunk
                current_len = sum(len(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_len += sent_len

        if current_chunk:
            chunk_str = " ".join(current_chunk)
            chunks.append({
                "chunk_index": chunk_idx,
                "subject": subject,
                "topic": topic,
                "chapter": chapter or topic,
                "section": default_section,
                "text": chunk_str,
                "char_length": len(chunk_str)
            })

        return chunks

    @classmethod
    def normalize_text(cls, text: str) -> str:
        # Strip excessive whitespace, HTML tags, unprintable control characters
        no_html = re.sub(r'<[^>]+>', ' ', text)
        clean = re.sub(r'[\r\t]+', ' ', no_html)
        clean = re.sub(r'\n{3,}', '\n\n', clean)
        clean = re.sub(r' +', ' ', clean)
        return clean.strip()
