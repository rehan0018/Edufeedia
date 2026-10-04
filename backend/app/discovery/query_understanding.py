"""
Intent Interpreter and Query Expansion Engine.
Extracts Subject, Topic, Grade (Class 1-12), Board, Depth, Format Preference,
and expands academic keywords to bridge the gap between student questions and authoritative curriculum sources.
"""

import re
from typing import Dict, Any, List, Optional
from app.schemas.schemas import InterpretedIntent

class QueryUnderstandingEngine:
    """
    Parses natural language student search queries into structured educational intent
    and performs curriculum-aware query expansion.
    """

    GRADE_PATTERNS = [
        (re.compile(r"\bclass\s*([0-9]{1,2})\b", re.IGNORECASE), 1),
        (re.compile(r"\bgrade\s*([0-9]{1,2})\b", re.IGNORECASE), 1),
        (re.compile(r"\bstd\s*([0-9]{1,2})\b", re.IGNORECASE), 1),
        (re.compile(r"\b([0-9]{1,2})(?:st|nd|rd|th)\s*(?:grade|class|standard)\b", re.IGNORECASE), 1),
        (re.compile(r"\bclass\s*(x|xi|xii|ix|viii|vii|vi|v|iv|iii|ii|i)\b", re.IGNORECASE), "roman"),
    ]

    ROMAN_NUMERALS = {
        "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6,
        "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12
    }

    BOARD_KEYWORDS = {
        "cbse": "CBSE",
        "icse": "ICSE",
        "ncert": "CBSE",
        "state board": "State_Board",
        "maharashtra board": "State_Board",
        "ib": "IB",
        "igcse": "IGCSE"
    }

    SUBJECT_KEYWORDS = {
        "physics": "Physics",
        "chemistry": "Chemistry",
        "biology": "Biology",
        "science": "Science",
        "math": "Mathematics",
        "mathematics": "Mathematics",
        "algebra": "Mathematics",
        "geometry": "Mathematics",
        "calculus": "Mathematics",
        "history": "Social Science",
        "geography": "Social Science",
        "civics": "Social Science",
        "computer": "Computer Science",
        "coding": "Computer Science",
        "python": "Computer Science",
        "astronomy": "Space Science"
    }

    DEPTH_KEYWORDS = {
        "jee": "advanced",
        "neet": "advanced",
        "olympiad": "advanced",
        "derivation": "advanced",
        "deep dive": "advanced",
        "proof": "advanced",
        "simple": "introductory",
        "basics": "introductory",
        "beginner": "introductory",
        "cartoon": "introductory",
        "for kids": "introductory",
        "for beginners": "introductory"
    }

    FORMAT_KEYWORDS = {
        "cartoon": "animation",
        "animation": "animation",
        "animated": "animation",
        "video": "video",
        "simulation": "interactive_sim",
        "experiment": "interactive_sim",
        "sim": "interactive_sim",
        "interactive": "interactive_sim",
        "read": "reading",
        "notes": "reading",
        "textbook": "reading",
        "ncert book": "reading",
        "quiz": "quiz",
        "test": "quiz",
        "mcq": "quiz",
        "questions": "quiz"
    }

    TOPIC_EXPANSION_KNOWLEDGE_BASE = {
        "photosynthesis": {
            "subject": "Biology",
            "default_grade": 8,
            "terms": [
                "chloroplast", "chlorophyll", "stomata", "light reaction", "dark reaction",
                "carbon dioxide and water", "glucose production", "autotrophic nutrition",
                "NCERT Science Chapter Nutrition in Plants", "thylakoid", "calvin cycle"
            ],
            "prerequisites": ["Plant Cells", "Light and Energy", "Chemical Reactions"],
            "advanced": ["Calvin Cycle", "Light Dependent Reactions", "Photosystems I and II"]
        },
        "newton's laws": {
            "subject": "Physics",
            "default_grade": 9,
            "terms": [
                "force and laws of motion", "inertia", "momentum", "f=ma",
                "action and reaction", "balanced and unbalanced forces", "conservation of momentum"
            ],
            "prerequisites": ["Velocity and Acceleration", "Force and Motion"],
            "advanced": ["Friction Co-efficient", "Circular Dynamics", "Impulse-Momentum Theorem"]
        },
        "gravity": {
            "subject": "Physics",
            "default_grade": 9,
            "terms": [
                "universal law of gravitation", "gravitational constant G", "free fall",
                "acceleration due to gravity g", "mass vs weight", "planetary orbits"
            ],
            "prerequisites": ["Force", "Newton's Second Law", "Distance and Displacement"],
            "advanced": ["Gravitational Potential Energy", "Escape Velocity", "Kepler's Three Laws"]
        },
        "cell structure": {
            "subject": "Biology",
            "default_grade": 8,
            "terms": [
                "plant cell vs animal cell", "mitochondria", "nucleus", "cell membrane",
                "cytoplasm", "vacuole", "endoplasmic reticulum", "golgi apparatus"
            ],
            "prerequisites": ["Living Organisms", "Microscopes"],
            "advanced": ["Cell Division (Mitosis & Meiosis)", "Membrane Transport", "ATP Synthesis"]
        },
        "quadratic equations": {
            "subject": "Mathematics",
            "default_grade": 10,
            "terms": [
                "standard form ax^2 + bx + c = 0", "discriminant b^2 - 4ac",
                "nature of roots", "factoring method", "quadratic formula", "completing the square"
            ],
            "prerequisites": ["Linear Equations", "Polynomials", "Algebraic Identities"],
            "advanced": ["Roots of Unity", "Conic Sections", "Optimization Word Problems"]
        },
        "periodic table": {
            "subject": "Chemistry",
            "default_grade": 10,
            "terms": [
                "modern periodic law", "atomic radius", "valency and valence electrons",
                "metals and non-metals", "electronegativity", "groups and periods"
            ],
            "prerequisites": ["Atomic Structure", "Protons and Neutrons", "Chemical Bonding"],
            "advanced": ["Orbital Hybridization", "Ionization Enthalpy", "Transition Metals"]
        }
    }

    @classmethod
    def interpret_query(
        cls,
        query: str,
        student_grade: Optional[int] = None,
        student_board: Optional[str] = None
    ) -> InterpretedIntent:
        """
        Parses raw text query, resolves grade/board/subject/topic, and returns structured intent.
        """
        clean_q = query.strip()
        lower_q = clean_q.lower()

        # 1. Extract Grade
        extracted_grade = None
        for pattern, kind in cls.GRADE_PATTERNS:
            match = pattern.search(lower_q)
            if match:
                val = match.group(1).lower()
                if kind == "roman" and val in cls.ROMAN_NUMERALS:
                    extracted_grade = cls.ROMAN_NUMERALS[val]
                    break
                elif val.isdigit():
                    extracted_grade = int(val)
                    break
        grade_level = extracted_grade or student_grade or 8

        # 2. Extract Board
        board = student_board or "CBSE"
        for kw, bd in cls.BOARD_KEYWORDS.items():
            if kw in lower_q:
                board = bd
                break

        # 3. Extract Format Preference
        format_pref = None
        for kw, fmt in cls.FORMAT_KEYWORDS.items():
            if kw in lower_q:
                format_pref = fmt
                break

        # 4. Extract Depth
        depth = "standard"
        for kw, dp in cls.DEPTH_KEYWORDS.items():
            if kw in lower_q:
                depth = dp
                break

        # 5. Extract Language
        language = "en"
        if any(w in lower_q for w in ["hindi", "in hindi", "hindi me", "hindi mein"]):
            language = "hi"

        # 6. Extract Topic & Subject
        detected_topic = clean_q
        detected_subject = "Science"
        expanded_terms = []

        # Strip command prefixes like "explain", "what is", "how do", "class 8", etc.
        strip_pattern = re.compile(
            r"\b(explain|what is|how do|describe|define|teach me|notes for|quiz on|summary of|for class \d+|class \d+|cbse|icse)\b",
            re.IGNORECASE
        )
        core_topic_candidate = strip_pattern.sub("", lower_q).strip()

        # Check knowledge base for exact or partial matches
        matched_kb = None
        for kb_key, kb_data in cls.TOPIC_EXPANSION_KNOWLEDGE_BASE.items():
            raw_words = kb_key.replace("'", " ").split()
            key_words = [w for w in raw_words if len(w) > 3] + [w.rstrip("s") for w in raw_words if len(w) > 4]
            if (kb_key in lower_q or
                any(term.lower() in lower_q for term in kb_data["terms"][:4]) or
                any(kw in lower_q for kw in key_words)):
                matched_kb = (kb_key, kb_data)
                break

        if matched_kb:
            kb_key, kb_data = matched_kb
            detected_topic = kb_key.title()
            detected_subject = kb_data["subject"]
            expanded_terms = kb_data["terms"]
        else:
            # Fallback subject detection from keywords
            for kw, subj in cls.SUBJECT_KEYWORDS.items():
                if kw in lower_q:
                    detected_subject = subj
                    break
            detected_topic = (core_topic_candidate.title() if core_topic_candidate else clean_q)
            expanded_terms = [detected_topic, f"{detected_topic} {board} Class {grade_level}", f"{detected_topic} NCERT"]

        if any(term in lower_q for term in ["numerical", "numericals", "problem", "solve", "derivation", "formula"]):
            intent_type = "problem_solving"
        elif format_pref == "quiz" or "quiz" in lower_q or "mcq" in lower_q:
            intent_type = "quiz"
        else:
            intent_type = "explanation"

        return InterpretedIntent(
            subject=detected_subject,
            topic=detected_topic,
            subtopic=None,
            grade_level=grade_level,
            board=board,
            intent_type=intent_type,
            depth_level=depth,
            format_preference=format_pref,
            language=language,
            expanded_terms=expanded_terms,
            confidence=0.95
        )
