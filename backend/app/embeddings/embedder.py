import math
import re
import hashlib
from typing import List, Dict, Any, Optional

VECTOR_DIMENSION = 64

class SemanticEmbedder:
    """
    Semantic Embedder for Edufeedia content and student interest profiles.
    Generates L2-normalized dense vector representations with semantic term clustering.
    """

    def __init__(self, dim: int = VECTOR_DIMENSION):
        self.dim = dim

    def _hash_token(self, token: str) -> int:
        return int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % self.dim

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dim

        text_clean = text.lower()
        tokens = re.findall(r'\b[a-zA-Z0-9_\-\^]+\b', text_clean)
        if not tokens:
            return [0.0] * self.dim

        vec = [0.0] * self.dim

        # 1. Unigram token projection
        for token in tokens:
            idx = self._hash_token(token)
            weight = 3.0 if len(token) > 3 else 1.0
            vec[idx] += weight

            # Subword character 3-grams for morphological similarity
            if len(token) >= 4:
                for j in range(len(token) - 2):
                    sub = token[j:j+3]
                    sub_idx = self._hash_token(sub)
                    vec[sub_idx] += 1.0

        # 2. Bigram contextual projection
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            idx = self._hash_token(bigram)
            vec[idx] += 2.0

        # 3. L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 5) for x in vec]
        else:
            vec = [0.0] * self.dim

        return vec

    def embed_content(
        self,
        title: str,
        description: str = "",
        subject: str = "",
        topic: str = "",
        tags: Optional[List[str]] = None
    ) -> List[float]:
        # Weighted composition: Subject & Topic (3x), Title (2x), Description (1x), Tags (2x)
        weighted_chunks = [
            f"{subject} {topic} " * 3,
            f"{title} " * 2,
            f"{' '.join(tags or [])} " * 2,
            description or ""
        ]
        return self.embed_text(" ".join(weighted_chunks))

    def embed_student_profile(
        self,
        interests: List[str],
        board: str = "CBSE",
        grade_level: int = 10,
        completed_topics: Optional[List[str]] = None
    ) -> List[float]:
        profile_text = f"{board} Grade {grade_level} {' '.join(interests)} {' '.join(completed_topics or [])}"
        return self.embed_text(profile_text)

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        sim = dot / (norm_a * norm_b)
        # Bound between [0.0, 1.0] for recommendation scoring
        return max(0.0, min(1.0, round(float(sim), 4)))

embedder_instance = SemanticEmbedder()

def embed_text(text: str) -> List[float]:
    return embedder_instance.embed_text(text)

def embed_content(title: str, description: str = "", subject: str = "", topic: str = "", tags: Optional[List[str]] = None) -> List[float]:
    return embedder_instance.embed_content(title, description, subject, topic, tags)

def embed_student(interests: List[str], board: str = "CBSE", grade_level: int = 10, completed_topics: Optional[List[str]] = None) -> List[float]:
    return embedder_instance.embed_student_profile(interests, board, grade_level, completed_topics)

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    return SemanticEmbedder.cosine_similarity(vec_a, vec_b)
