import math
import re
import hashlib
from typing import List, Dict, Any, Optional

VECTOR_DIMENSION = 384

# Semantic Concept Clusters across school curricula (Grades 6–12)
# Activating related dense dimensional subspaces for semantic synonym matching
SEMANTIC_CLUSTERS = {
    # Physics - Dynamics & Motion
    "physics_dynamics": {
        "dim_range": (0, 32),
        "concepts": ["force", "mass", "acceleration", "newton", "second law", "f=ma", "inertia", "momentum", "motion", "gravity", "weight", "velocity", "friction"]
    },
    # Physics - Energy & Optics
    "physics_energy_optics": {
        "dim_range": (32, 64),
        "concepts": ["energy", "work", "power", "kinetic", "potential", "light", "optics", "reflection", "refraction", "lens", "mirror", "photon", "wavelength"]
    },
    # Chemistry - Bonding & Periodic Trends
    "chemistry_bonding": {
        "dim_range": (64, 96),
        "concepts": ["chemical", "bonding", "periodic", "table", "electron", "proton", "neutron", "ionic", "covalent", "electronegativity", "atomic radius", "octet", "molecule", "reaction"]
    },
    # Biology - Respiration & Metabolism
    "biology_respiration": {
        "dim_range": (96, 128),
        "concepts": ["respiration", "cellular", "glucose", "atp", "oxygen", "alveoli", "mitochondria", "aerobic", "anaerobic", "lungs", "gas exchange", "glycolysis", "fermentation"]
    },
    # Biology - Genetics & Cells
    "biology_genetics": {
        "dim_range": (128, 160),
        "concepts": ["dna", "rna", "genetics", "gene", "chromosome", "cell", "nucleus", "membrane", "mitosis", "meiosis", "heredity", "trait", "mutation"]
    },
    # Mathematics - Quadratic & Algebra
    "math_algebra": {
        "dim_range": (160, 192),
        "concepts": ["quadratic", "equation", "roots", "discriminant", "factorization", "parabola", "algebra", "polynomial", "linear", "variable", "coefficient", "zeros"]
    },
    # Mathematics - Trigonometry & Geometry
    "math_trig_geometry": {
        "dim_range": (192, 224),
        "concepts": ["trigonometry", "sin", "cos", "tan", "triangle", "hypotenuse", "pythagoras", "angle", "geometry", "circle", "radius", "area", "perimeter"]
    },
    # Computer Science - Python & Algorithms
    "cs_programming": {
        "dim_range": (224, 256),
        "concepts": ["python", "function", "loop", "for", "while", "variable", "list", "dictionary", "array", "recursion", "algorithm", "code", "programming", "data structure"]
    },
    # Computer Science - AI & Machine Learning
    "cs_ai_ml": {
        "dim_range": (256, 288),
        "concepts": ["machine learning", "artificial intelligence", "neural", "network", "model", "training", "dataset", "deep learning", "prediction", "classification", "weights"]
    },
    # Space Science - Orbital Mechanics & Astronomy
    "space_astronomy": {
        "dim_range": (288, 320),
        "concepts": ["space", "astronomy", "orbit", "kepler", "planet", "solar system", "sun", "galaxy", "satellite", "black hole", "telescope", "gravitation", "perihelion"]
    },
    # General Pedagogy & Scientific Inquiry
    "pedagogy_inquiry": {
        "dim_range": (320, 352),
        "concepts": ["experiment", "hypothesis", "analysis", "proof", "derivation", "formula", "concept", "definition", "example", "step-by-step", "tutorial", "lesson"]
    }
}

class SemanticEmbedder:
    """
    384-Dimensional Semantic Dense Sentence Embedder.
    Supports dynamic Sentence-Transformer neural model loading (e.g. all-MiniLM-L6-v2)
    with seamless fallback to calibrated 384-d semantic concept subspace projection.
    """

    def __init__(self, dim: int = VECTOR_DIMENSION, model_name: str = "all-MiniLM-L6-v2"):
        self.dim = dim
        self.model_name = model_name
        self._transformer_model = None
        self._is_transformer_active = False

        # Attempt to load transformer model if sentence_transformers package is available
        try:
            from sentence_transformers import SentenceTransformer
            self._transformer_model = SentenceTransformer(self.model_name)
            self._is_transformer_active = True
        except Exception:
            # Operates on deterministic 384-d semantic concept subspace projection
            self._is_transformer_active = False

    def _hash_token(self, token: str, seed: int = 0) -> int:
        raw = f"{token}:{seed}".encode('utf-8')
        return int(hashlib.md5(raw).hexdigest(), 16) % self.dim

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dim

        # 1. Neural Transformer Pathway (if available)
        if self._is_transformer_active and self._transformer_model is not None:
            try:
                emb = self._transformer_model.encode(text, convert_to_numpy=True)
                return [round(float(x), 5) for x in emb.tolist()[:self.dim]]
            except Exception:
                pass

        # 2. Calibrated 384-d Semantic Concept Projection Pathway

        text_clean = text.lower()
        tokens = re.findall(r'\b[a-zA-Z0-9_\-\^]+\b', text_clean)
        if not tokens:
            return [0.0] * self.dim

        vec = [0.0] * self.dim

        # 1. Base Lexical & Subword Projection (Dimensions 352 to 383 + General Hashing)
        for token in tokens:
            idx1 = self._hash_token(token, seed=1)
            idx2 = self._hash_token(token, seed=2)
            weight = 2.5 if len(token) > 3 else 1.0
            vec[idx1] += weight
            vec[idx2] += (weight * 0.5)

            # Subword character 3-grams for morphological handling
            if len(token) >= 4:
                for j in range(len(token) - 2):
                    sub = token[j:j+3]
                    sub_idx = self._hash_token(sub, seed=3)
                    vec[sub_idx] += 0.8

        # 2. Bigram Contextual Projection
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            idx = self._hash_token(bigram, seed=4)
            vec[idx] += 1.8

        # 3. Dense Semantic Subspace Projection
        # Activates dedicated semantic dimensions when matching conceptual synonyms
        for cluster_name, cluster_data in SEMANTIC_CLUSTERS.items():
            start_dim, end_dim = cluster_data["dim_range"]
            cluster_width = end_dim - start_dim
            matches = 0
            for concept in cluster_data["concepts"]:
                if concept in text_clean:
                    matches += 1
                    # Spread semantic weight across this cluster's dedicated subspace
                    concept_idx = start_dim + (self._hash_token(concept, seed=5) % cluster_width)
                    vec[concept_idx] += 4.0

            if matches > 0:
                # Add uniform baseline energy across cluster subspace to capture high-level domain
                cluster_boost = min(3.0, matches * 0.8)
                for d in range(start_dim, end_dim):
                    vec[d] += cluster_boost

        # 4. L2 Normalization onto Unit Hypersphere
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
        # Bound between [0.0, 1.0] for scoring
        return max(0.0, min(1.0, round(float(sim), 4)))

embedder_instance = SemanticEmbedder()

def embed_text(text: str) -> List[float]:
    return embedder_instance.embed_text(text)

def embed_query(query: str) -> List[float]:
    return embedder_instance.embed_text(query)

def embed_content(title: str, description: str = "", subject: str = "", topic: str = "", tags: Optional[List[str]] = None) -> List[float]:
    return embedder_instance.embed_content(title, description, subject, topic, tags)

def embed_student(interests: List[str], board: str = "CBSE", grade_level: int = 10, completed_topics: Optional[List[str]] = None) -> List[float]:
    return embedder_instance.embed_student_profile(interests, board, grade_level, completed_topics)

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    return SemanticEmbedder.cosine_similarity(vec_a, vec_b)
