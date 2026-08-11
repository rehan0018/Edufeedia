import re
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import ContentItem
from app.embeddings.embedder import embed_query, embed_content, cosine_similarity
from app.ai.llm_client import llm_client

logger = logging.getLogger(__name__)

# Comprehensive Curriculum Document Chunks (Structured across CBSE / ICSE Grades 6–12)
CURRICULUM_DOCUMENT_CORPUS = [
    # Mathematics — Quadratic Equations (CBSE G10 Chapter 4)
    {
        "doc_id": "math_quad_def",
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "section": "Core Definition & Roots Formula",
        "text": "A quadratic equation in variable x is an equation of the form ax² + bx + c = 0, where a, b, c are real numbers and a ≠ 0. The solutions are called roots and given by the quadratic formula x = (-b ± √(b² - 4ac)) / (2a)."
    },
    {
        "doc_id": "math_quad_disc",
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "section": "Nature of Roots & Discriminant",
        "text": "The expression D = b² - 4ac is called the discriminant. If D > 0, there are two distinct real roots. If D = 0, there are two equal real roots (x = -b / 2a). If D < 0, there are no real roots (roots are complex conjugate numbers)."
    },
    {
        "doc_id": "math_quad_app",
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "section": "Real-World Trajectory Applications",
        "text": "Quadratic functions y = ax² + bx + c graph as symmetrical parabolas. Projectile motion, satellite dish curvatures, and profit-maximization curves are modeled using quadratic vertices."
    },

    # Science — Human Respiration & Bioenergetics (CBSE G10 Chapter 6)
    {
        "doc_id": "sci_resp_aerobic",
        "subject": "Science",
        "topic": "Human Respiration",
        "grade": 10,
        "section": "Aerobic Cellular Respiration & ATP",
        "text": "Aerobic respiration breaks down glucose in the presence of oxygen inside mitochondria to produce carbon dioxide, water, and 36-38 molecules of ATP: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + ATP. ATP provides the direct chemical energy for cellular metabolic activities."
    },
    {
        "doc_id": "sci_resp_anaerobic",
        "subject": "Science",
        "topic": "Human Respiration",
        "grade": 10,
        "section": "Anaerobic Respiration & Gas Diffusion",
        "text": "When oxygen supply is insufficient during heavy muscular exertion, pyruvate converts to lactic acid in cytoplasm, causing muscle fatigue. Alveoli in the lungs possess ultra-thin single-cell walls wrapped in extensive capillary networks to maximize gaseous diffusion."
    },

    # Science — Chemical Bonding & Periodic Trends (CBSE G10 Chapter 3/5)
    {
        "doc_id": "sci_chem_ionic",
        "subject": "Science",
        "topic": "Chemical Bonding",
        "grade": 10,
        "section": "Ionic Bonding & Octet Stability",
        "text": "Atoms bond to achieve inert gas electronic configuration (stable octet). Ionic bonds form through complete transfer of valence electrons from an electropositive metal to an electronegative non-metal (e.g. Na⁺ + Cl⁻ → NaCl), resulting in high melting point crystalline lattices."
    },
    {
        "doc_id": "sci_chem_covalent",
        "subject": "Science",
        "topic": "Chemical Bonding",
        "grade": 10,
        "section": "Covalent Bonding & Electronegativity Trends",
        "text": "Covalent bonds form by sharing electron pairs between non-metallic atoms. Electronegativity increases across a period (left to right) and decreases down a group, determining whether shared bonds are non-polar covalent or polar covalent."
    },

    # Science — Newton's Laws & Dynamics (CBSE G9/G11 Chapter 9)
    {
        "doc_id": "sci_phys_newton2",
        "subject": "Science",
        "topic": "Newton's Laws",
        "grade": 10,
        "section": "Second Law of Motion (F = ma)",
        "text": "Newton's Second Law states that the rate of change of momentum of a body is directly proportional to the applied unbalanced force: F = dp/dt = m(v - u)/t = ma. Force is measured in Newtons (kg·m/s²)."
    },
    {
        "doc_id": "sci_phys_newton1_3",
        "subject": "Science",
        "topic": "Newton's Laws",
        "grade": 10,
        "section": "First and Third Laws of Motion",
        "text": "Newton's First Law (Law of Inertia) states an object maintains constant velocity unless a net external force acts. The Third Law states that every action has an equal and opposite reaction acting on separate interacting bodies."
    },

    # Computer Science — Python Fundamentals & Data Structures
    {
        "doc_id": "cs_py_functions",
        "subject": "Computer Science",
        "topic": "Python Basics",
        "grade": 10,
        "section": "Functions & Modular Scope",
        "text": "In Python, functions defined with 'def' create modular, reusable code blocks. Parameters receive input arguments, local variables have block scope, and the 'return' statement sends values back to the caller."
    },
    {
        "doc_id": "cs_py_loops_data",
        "subject": "Computer Science",
        "topic": "Python Basics",
        "grade": 10,
        "section": "Iteration Loops & Mutable Collections",
        "text": "Python supports 'for' loops iterating over sequences and 'while' loops testing conditional logic. Lists are mutable ordered sequences, whereas dictionaries store key-value mappings with O(1) average lookup times."
    },

    # Space Science — Planetary Orbits & Gravitation
    {
        "doc_id": "space_kepler_gravity",
        "subject": "Space Science",
        "topic": "Orbital Mechanics",
        "grade": 10,
        "section": "Kepler's Laws & Gravitational Centripetal Forces",
        "text": "Kepler's laws state that planetary orbits are elliptical with the Sun at one focus, and equal areas are swept in equal time. The gravitational attraction F = G(m₁m₂)/r² provides the necessary centripetal force (mv²/r) to maintain stable planetary orbits."
    }
]

class RAGEngine:
    """
    Hybrid RAG Engine combining 384-dimensional Dense Vector Similarity,
    BM25 Lexical Keyword Matching, and Reciprocal Rank Fusion (RRF) Reranking.
    """

    @classmethod
    def query_rag_tutor(
        cls,
        db: Session,
        question: str,
        content_item_id: Optional[str] = None,
        student_grade: int = 10
    ) -> Dict[str, Any]:
        # 1. Retrieve specific lesson context if content_item_id is provided
        lesson_context = ""
        topic_name = "Curriculum Concept"
        if content_item_id:
            item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
            if item:
                lesson_context = f"Lesson: {item.title}. Topic: {item.topic} ({item.subject}). Description: {item.description or ''}."
                topic_name = item.topic

        # 2. Hybrid Retrieval (Dense Vector + BM25 Lexical)
        top_chunks = cls._hybrid_retrieve_chunks(question, db=db, top_k=2)

        # 3. Assemble Curriculum Context
        curriculum_context_pieces = [lesson_context] if lesson_context else []
        for chunk, score in top_chunks:
            curriculum_context_pieces.append(f"[{chunk['topic']} - {chunk['section']}]: {chunk['text']}")
            if topic_name == "Curriculum Concept":
                topic_name = chunk["topic"]

        assembled_context = "\n".join(curriculum_context_pieces)

        # 4. Generate Socratic Guidance via LLM Client
        response = llm_client.generate_socratic_response(
            question=question,
            curriculum_context=assembled_context,
            topic=topic_name,
            student_grade=student_grade
        )

        return response

    @classmethod
    def _hybrid_retrieve_chunks(cls, query: str, db: Optional[Session] = None, top_k: int = 2) -> List[Tuple[Dict[str, Any], float]]:
        query_clean = query.lower()
        query_terms = set(re.findall(r'\b[a-z]{3,}\b', query_clean))
        query_vec = embed_query(query)
        # Merge in-memory verified corpus with dynamic database chunks
        active_corpus = list(CURRICULUM_DOCUMENT_CORPUS)
        if db is not None:
            try:
                from app.models.models import CurriculumChunk
                db_chunks = db.query(CurriculumChunk).all()
                for dbc in db_chunks:
                    active_corpus.append({
                        "doc_id": dbc.id,
                        "subject": dbc.subject,
                        "topic": dbc.topic,
                        "grade": dbc.grade_level,
                        "section": dbc.section,
                        "text": dbc.chunk_text
                    })
            except Exception as e:
                logger.warning("[RAG Database Chunk Query Warning]: %s", e)

        # --- A. Dense Vector Similarity Scoring ---
        dense_scores = []
        for idx, doc in enumerate(active_corpus):
            doc_vec = embed_content(doc["topic"], doc["text"], doc["subject"], doc["section"])
            sim = cosine_similarity(query_vec, doc_vec)
            dense_scores.append((idx, sim))
        dense_scores.sort(key=lambda x: x[1], reverse=True)

        # --- B. Calibrated Okapi BM25 Lexical Scoring (k1=1.2, b=0.75) ---
        N = max(1, len(active_corpus))
        doc_token_lists = [
            re.findall(r'\b[a-z]{3,}\b', f"{doc['topic']} {doc['section']} {doc['text']}".lower())
            for doc in active_corpus
        ]
        doc_lens = [max(1, len(tokens)) for tokens in doc_token_lists]
        avgdl = sum(doc_lens) / N

        k1 = 1.2
        b = 0.75

        lexical_scores = []
        for idx, tokens in enumerate(doc_token_lists):
            score = 0.0
            doc_len = doc_lens[idx]
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            for q_term in query_terms:
                if q_term in token_counts:
                    freq = token_counts[q_term]
                    df = sum(1 for t_list in doc_token_lists if q_term in t_list)
                    idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                    tf = (freq * (k1 + 1.0)) / (freq + k1 * (1.0 - b + b * (doc_len / avgdl)))
                    score += (idf * tf)

            lexical_scores.append((idx, round(score, 4)))
        lexical_scores.sort(key=lambda x: x[1], reverse=True)

        # --- C. Reciprocal Rank Fusion (RRF) Reranking ---
        rrf_scores = {}
        k_const = 60.0

        for rank, (doc_idx, _) in enumerate(dense_scores):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (k_const + rank + 1))

        for rank, (doc_idx, _) in enumerate(lexical_scores):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (1.0 / (k_const + rank + 1))

        # Sort by final RRF score
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_idx, score in sorted_rrf[:top_k]:
            results.append((active_corpus[doc_idx], round(score, 4)))

        return results
