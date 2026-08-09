from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.models import ContentItem
from app.embeddings.embedder import embed_query, embed_content, cosine_similarity
from app.ai.llm_client import llm_client

CURRICULUM_KNOWLEDGE_STORE = [
    {
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "chunk_id": "math_quad_01",
        "text": "The standard form of a quadratic equation is ax² + bx + c = 0 (a ≠ 0). The roots are given by x = (-b ± √(b² - 4ac)) / (2a). The discriminant D = b² - 4ac determines root character: D > 0 gives two real distinct roots; D = 0 gives one repeated real root; D < 0 gives complex conjugate roots."
    },
    {
        "subject": "Science",
        "topic": "Human Respiration",
        "grade": 10,
        "chunk_id": "sci_resp_01",
        "text": "Cellular respiration breaks down glucose in the presence of oxygen to release chemical energy (ATP). Aerobic respiration occurs in cytoplasm (glycolysis) and mitochondria (Krebs cycle and electron transport chain), producing up to 38 ATP per glucose molecule. Alveoli are thin-walled sacs surrounded by blood capillaries to maximize diffusion."
    },
    {
        "subject": "Science",
        "topic": "Chemical Bonding",
        "grade": 10,
        "chunk_id": "sci_chem_01",
        "text": "Chemical bonds form between atoms to achieve stable octet configurations. Ionic bonding involves complete electrostatic electron transfer between metals and non-metals. Covalent bonding involves sharing electron pairs between non-metals. Electronegativity differences determine bond polarity."
    },
    {
        "subject": "Science",
        "topic": "Newton's Laws",
        "grade": 10,
        "chunk_id": "sci_phys_01",
        "text": "Newton's First Law (Law of Inertia) states an object remains at rest or in uniform straight-line motion unless acted on by an external net force. Newton's Second Law defines force as rate of change of momentum (F = ma). Newton's Third Law states every action has an equal and opposite reaction acting on different bodies."
    },
    {
        "subject": "Computer Science",
        "topic": "Python Basics",
        "grade": 10,
        "chunk_id": "cs_py_01",
        "text": "Python is an interpreted, dynamically typed programming language. Functions defined with 'def' accept parameters, execute scoped blocks, and return values. 'for' and 'while' loops handle iterations. Lists and dictionaries provide mutable ordered and key-value data structures."
    },
    {
        "subject": "Space Science",
        "topic": "Orbital Mechanics",
        "grade": 10,
        "chunk_id": "space_orbit_01",
        "text": "Kepler's First Law states planetary orbits are ellipses with the Sun at one focus. Kepler's Second Law states equal areas are swept in equal time intervals, meaning planets move faster at perihelion than at aphelion. Gravitational attraction F = G(m₁m₂)/r² provides the centripetal acceleration holding satellites in stable orbit."
    }
]

class RAGEngine:
    """
    Curriculum Retrieval-Augmented Generation Engine for Edufeedia.
    Matches student inquiries against verified curriculum chunks and dynamically
    constructs safe Socratic pedagogical responses.
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
        topic_name = "Curriculum Review"
        if content_item_id:
            item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
            if item:
                lesson_context = f"Lesson: {item.title}. Topic: {item.topic} ({item.subject}). Description: {item.description or ''}."
                topic_name = item.topic

        # 2. Vector Semantic Retrieval across Curriculum Chunks
        query_vec = embed_query(question)
        scored_chunks = []
        for chunk in CURRICULUM_KNOWLEDGE_STORE:
            chunk_vec = embed_content(chunk["topic"], chunk["text"], chunk["subject"], chunk["topic"])
            sim = cosine_similarity(query_vec, chunk_vec)
            scored_chunks.append((sim, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunk = scored_chunks[0][1] if scored_chunks else None

        combined_curriculum_context = lesson_context
        if top_chunk:
            combined_curriculum_context += f" Verified Knowledge: {top_chunk['text']}"
            if topic_name == "Curriculum Review":
                topic_name = top_chunk["topic"]

        # 3. Synthesize Socratic response via LLM client
        response = llm_client.generate_socratic_response(
            question=question,
            curriculum_context=combined_curriculum_context,
            topic=topic_name,
            student_grade=student_grade
        )

        return response
