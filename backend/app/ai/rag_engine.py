import re
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import ContentItem
from app.embeddings.embedder import embed_query, embed_content, cosine_similarity
from app.ai.llm_client import llm_client

logger = logging.getLogger(__name__)

# Persistent in-memory cache for curriculum embeddings to prevent per-query recomputation
_CHUNK_EMBEDDING_CACHE: Dict[str, List[float]] = {}

# Comprehensive Curriculum Document Chunks (Structured across CBSE / ICSE Grades 6–12)
CURRICULUM_DOCUMENT_CORPUS = [
    # Computer Science — Computer Networks & Internet (CBSE Class 10/12)
    {
        "doc_id": "cs_net_intro",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "Network Fundamentals & Topologies",
        "text": "A computer network is an interconnected group of computing devices (nodes) that communicate and share resources (data, printers, storage) via transmission media (guided cables like fiber optics or unguided wireless radio waves). Common topologies include Star, Bus, Mesh, and Ring."
    },
    {
        "doc_id": "cs_net_types",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "LAN, MAN, WAN & Network Scales",
        "text": "Networks are categorized by geographic scale: Local Area Network (LAN) spans a room or school campus; Metropolitan Area Network (MAN) spans a city; Wide Area Network (WAN), such as the global Internet, spans across countries and continents using satellite and submarine cable backbones."
    },
    {
        "doc_id": "cs_net_osi_tcp",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "OSI 7-Layer Model & TCP/IP Protocol Suite",
        "text": "The OSI model standardizes network communication into 7 layers: Physical, Data Link, Network (IP addressing/routing), Transport (TCP reliable byte streams / UDP), Session, Presentation, and Application (HTTP, DNS, SMTP). Packets travel down the sender's stack (encapsulation) and up the receiver's stack (decapsulation)."
    },
    {
        "doc_id": "cs_net_devices_dns",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "Network Hardware & DNS Resolution",
        "text": "Network hardware includes Routers (which forward packets across different IP subnets), Switches (which switch frames inside a LAN using MAC addresses), and Modems. The Domain Name System (DNS) acts as the phonebook of the internet, translating human-friendly domain names (e.g. edufeedia.org) into numerical IP addresses."
    },
    {
        "doc_id": "cs_net_cybersecurity",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "Network Security & Encryption",
        "text": "Network security protects transmission confidentiality, integrity, and availability. Firewalls filter unauthorized inbound/outbound packets, while HTTPS/TLS protocols encrypt web payloads using public-key cryptography to prevent packet sniffing and man-in-the-middle attacks."
    },

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

    # Science — Electricity & Circuits (CBSE G10 Chapter 12)
    {
        "doc_id": "sci_phys_circuits_ohm",
        "subject": "Science",
        "topic": "Electricity & Circuits",
        "grade": 10,
        "section": "Ohm's Law, Voltage & Current",
        "text": "Ohm's Law states that electric current I flowing through a conductor is directly proportional to the potential difference V across its ends at constant temperature: V = I × R. Resistance R is measured in Ohms (Ω) and depends on conductor length, cross-sectional area, and material resistivity."
    },
    {
        "doc_id": "sci_phys_resistors_comb",
        "subject": "Science",
        "topic": "Electricity & Circuits",
        "grade": 10,
        "section": "Series & Parallel Resistor Networks",
        "text": "In a series circuit, current is identical across all resistors and total resistance is R_total = R₁ + R₂ + R₃. In a parallel circuit, voltage is identical across all branches and equivalent reciprocal resistance is 1/R_total = 1/R₁ + 1/R₂ + 1/R₃."
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

    # Science — Chemical Reactions & Bonding (CBSE G10 Chapter 1/3)
    {
        "doc_id": "sci_chem_reactions",
        "subject": "Science",
        "topic": "Chemical Reactions",
        "grade": 10,
        "section": "Types of Chemical Reactions & Balancing",
        "text": "Chemical reactions involve breaking and making bonds to form new substances. Types include Combination, Decomposition, Single Displacement (more reactive metal displaces less reactive metal), Double Displacement (precipitation), and Redox (Oxidation is loss of electrons; Reduction is gain of electrons)."
    },
    {
        "doc_id": "sci_chem_bonding",
        "subject": "Science",
        "topic": "Chemical Bonding",
        "grade": 10,
        "section": "Ionic & Covalent Bonding Principles",
        "text": "Ionic bonds form by transferring electrons from electropositive metals to electronegative non-metals (e.g. NaCl), creating high melting point crystals. Covalent bonds form by sharing pairs of valence electrons between non-metals to achieve a stable octet (e.g. H₂O, CH₄)."
    },

    # Computer Science — Python Fundamentals & Data Structures
    {
        "doc_id": "cs_py_functions",
        "subject": "Computer Science",
        "topic": "Python Programming",
        "grade": 10,
        "section": "Functions & Modular Scope",
        "text": "In Python, functions defined with 'def' create modular, reusable code blocks. Parameters receive input arguments, local variables have block scope, and the 'return' statement sends values back to the caller."
    },
    {
        "doc_id": "cs_py_loops_data",
        "subject": "Computer Science",
        "topic": "Python Programming",
        "grade": 10,
        "section": "Iteration Loops & Mutable Collections",
        "text": "Python supports 'for' loops iterating over sequences and 'while' loops testing conditional logic. Lists are mutable ordered sequences, whereas dictionaries store key-value mappings with O(1) average lookup times."
    },

    # Mathematics — Trigonometry & Applications (CBSE G10 Chapter 8/9)
    {
        "doc_id": "math_trig_ratios",
        "subject": "Mathematics",
        "topic": "Trigonometry",
        "grade": 10,
        "section": "Trigonometric Ratios in Right Triangles",
        "text": "In a right-angled triangle with acute angle θ: sin(θ) = Opposite/Hypotenuse, cos(θ) = Adjacent/Hypotenuse, tan(θ) = Opposite/Adjacent = sin(θ)/cos(θ). Key fundamental identity: sin²(θ) + cos²(θ) = 1."
    }
]

class RAGEngine:
    """
    Intelligent Intent-Aware Hybrid RAG Engine combining:
    1. Query Topic & Intent Classification (Decouples query from open lesson)
    2. 384-dimensional Dense Vector Similarity
    3. Okapi BM25 Lexical Keyword Matching
    4. Reciprocal Rank Fusion (RRF) Reranking
    5. Relevance Gating & Socratic Synthesis
    """

    @classmethod
    def query_rag_tutor(
        cls,
        db: Session,
        question: str,
        content_item_id: Optional[str] = None,
        student_grade: int = 10
    ) -> Dict[str, Any]:
        # 1. Inspect Current Lesson (if open)
        current_lesson: Optional[ContentItem] = None
        if content_item_id:
            current_lesson = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()

        # 2. Intent & Relevance Classification
        # Does the student question actually relate to the open lesson, or is it an independent inquiry?
        is_lesson_related = False
        if current_lesson:
            is_lesson_related = cls._is_query_related_to_lesson(question, current_lesson)

        # 3. Hybrid Retrieval across Curriculum Chunks (Dense Vector + BM25 + RRF)
        top_chunks = cls._hybrid_retrieve_chunks(question, db=db, top_k=3)

        # 4. Determine Dynamic Topic & Scope Context
        subject_name = "General Science"
        if is_lesson_related and current_lesson:
            topic_name = current_lesson.topic
            subject_name = current_lesson.subject
            lesson_context = f"Active Lesson: {current_lesson.title} ({current_lesson.subject} - {current_lesson.topic}). Description: {current_lesson.description or ''}."
        elif top_chunks:
            best_chunk, best_score = top_chunks[0]
            topic_name = best_chunk["topic"]
            subject_name = best_chunk["subject"]
            lesson_context = f"Subject Domain: {best_chunk['subject']} — {best_chunk['topic']} ({best_chunk['section']})"
        else:
            topic_name = "General Curriculum"
            lesson_context = ""

        # 5. Assemble Curriculum Context
        curriculum_context_pieces = [lesson_context] if lesson_context else []
        for chunk, score in top_chunks:
            curriculum_context_pieces.append(f"[{chunk['subject']} - {chunk['topic']} ({chunk['section']})]: {chunk['text']}")

        assembled_context = "\n".join(curriculum_context_pieces)

        # 6. Generate Socratic Guidance via Model Gateway (OpenAI / Gemini / Local Socratic)
        response = llm_client.generate_socratic_response(
            question=question,
            curriculum_context=assembled_context,
            topic=topic_name,
            student_grade=student_grade,
            subject=subject_name
        )

        response["subject"] = subject_name
        response["topic"] = topic_name
        response["grade"] = student_grade
        response["grounding_source"] = f"{subject_name} • Grade {student_grade}"

        return response

    @classmethod
    def _is_query_related_to_lesson(cls, query: str, lesson: ContentItem) -> bool:
        """
        Determines whether the student's inquiry pertains to the open lesson
        or is a separate exploration topic.
        """
        q_clean = query.lower()
        lesson_terms = re.findall(r'\b[a-z]{3,}\b', f"{lesson.title} {lesson.topic} {lesson.subject} {lesson.description or ''}".lower())
        lesson_term_set = set(lesson_terms)
        
        query_terms = set(re.findall(r'\b[a-z]{3,}\b', q_clean))
        overlap = query_terms.intersection(lesson_term_set)

        # If there is meaningful lexical overlap with the lesson topic
        if len(overlap) >= 1 and any(t in lesson.topic.lower() or t in lesson.title.lower() for t in overlap):
            return True

        # Semantic cosine similarity check between query and lesson
        try:
            q_vec = embed_query(query)
            l_vec = embed_content(lesson.title, lesson.description or "", lesson.subject or "", lesson.topic or "")
            sim = cosine_similarity(q_vec, l_vec)
            return sim >= 0.48
        except Exception:
            return len(overlap) > 0

    @classmethod
    def _hybrid_retrieve_chunks(cls, query: str, db: Optional[Session] = None, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
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

        # --- A. Dense Vector Similarity Scoring with Embedding Cache ---
        dense_scores = []
        for idx, doc in enumerate(active_corpus):
            doc_key = f"{doc.get('subject')}:{doc.get('topic')}:{doc.get('section')}:{doc.get('text')[:80]}"
            if doc_key in _CHUNK_EMBEDDING_CACHE:
                doc_vec = _CHUNK_EMBEDDING_CACHE[doc_key]
            else:
                doc_vec = embed_content(doc["topic"], doc["text"], doc["subject"], doc["section"])
                _CHUNK_EMBEDDING_CACHE[doc_key] = doc_vec
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
