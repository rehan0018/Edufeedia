import re
import math
from typing import Dict, Any, List, Optional

SUBJECT_TOPIC_KEYWORDS = {
    "Mathematics": {
        "topics": ["Quadratic Equations", "Trigonometry", "Calculus", "Linear Equations", "Probability", "Coordinate Geometry", "Algebra", "Statistics"],
        "keywords": ["equation", "formula", "roots", "sin", "cos", "tan", "discriminant", "triangle", "theorem", "matrix", "polynomial", "graph", "variable"]
    },
    "Science": {
        "topics": ["Human Respiration", "Chemical Bonding", "Newton's Laws", "Electricity", "Light & Optics", "Genetics", "Acids & Bases", "Thermodynamics"],
        "keywords": ["cell", "atp", "oxygen", "glucose", "reaction", "electron", "periodic", "force", "mass", "acceleration", "gravity", "current", "voltage", "dna", "molecule"]
    },
    "Computer Science": {
        "topics": ["Python Basics", "Machine Learning", "Data Structures", "Algorithms", "Web Development", "Cybersecurity", "Artificial Intelligence"],
        "keywords": ["python", "function", "loop", "array", "list", "dictionary", "model", "neural", "binary", "code", "programming", "variable", "database"]
    },
    "Space Science": {
        "topics": ["Orbital Mechanics", "Solar System", "Black Holes", "Kepler's Laws", "Exoplanets", "Telescopes"],
        "keywords": ["planet", "orbit", "gravity", "sun", "galaxy", "telescope", "star", "satellite", "space", "astronomy", "cosmos"]
    }
}

class MetadataExtractor:
    """
    Extracts curriculum metadata, estimates grade-level suitability,
    and calculates readability and educational pedagogical quality scores.
    """

    @classmethod
    def extract_metadata(
        cls,
        title: str,
        description: str = "",
        raw_text: str = ""
    ) -> Dict[str, Any]:
        combined_text = f"{title} {description} {raw_text}".lower()

        # 1. Detect Subject and Topic
        subject, topic = cls._detect_subject_and_topic(combined_text)

        # 2. Compute Flesch-Kincaid Readability & Target Grade Level
        readability = cls._compute_readability(f"{title}. {description}. {raw_text[:500]}")

        # 3. Calculate Pedagogical Educational Score (0-100)
        edu_score = cls._compute_pedagogical_score(title, description, raw_text)

        # 4. Determine Recommended Board, Difficulty, and Syllabus Code
        difficulty = "medium"
        if readability["grade_level"] >= 11 or edu_score >= 95:
            difficulty = "hard"
        elif readability["grade_level"] <= 8 or edu_score < 75:
            difficulty = "easy"

        syllabus_code = cls._generate_syllabus_code("CBSE", readability["grade_level"], subject, topic)

        return {
            "subject": subject,
            "topic": topic,
            "curriculum_code": syllabus_code,
            "estimated_grade": max(6, min(12, readability["grade_level"])),
            "difficulty": difficulty,
            "readability_score": readability["flesch_reading_ease"],
            "reading_ease_description": readability["ease_label"],
            "edu_score": edu_score,
            "detected_keywords": cls._extract_top_keywords(combined_text)
        }

    @staticmethod
    def _generate_syllabus_code(board: str, grade: int, subject: str, topic: str) -> str:
        subj_code = "GEN"
        if "Math" in subject:
            subj_code = "MATH"
        elif "Science" in subject:
            subj_code = "SCI"
        elif "Computer" in subject:
            subj_code = "CS"
        elif "Space" in subject:
            subj_code = "SPACE"

        topic_clean = re.sub(r'[^A-Z0-9]', '', topic.upper())[:6]
        return f"{board}-G{grade}-{subj_code}-{topic_clean}"

    @classmethod
    def _detect_subject_and_topic(cls, text: str) -> (str, str):
        best_subject = "General Education"
        best_topic = "General Concept Review"
        max_subject_matches = 0

        for subj, data in SUBJECT_TOPIC_KEYWORDS.items():
            matches = sum(1 for kw in data["keywords"] if kw in text)
            if matches > max_subject_matches:
                max_subject_matches = matches
                best_subject = subj

                # Find best topic match
                for top in data["topics"]:
                    if top.lower() in text:
                        best_topic = top
                        break
                else:
                    best_topic = data["topics"][0]

        return best_subject, best_topic

    @staticmethod
    def _compute_readability(text: str) -> Dict[str, Any]:
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]

        num_words = max(1, len(words))
        num_sentences = max(1, len(sentences))

        # Approximate syllables
        def count_syllables(word):
            word = word.lower()
            syllable_count = len(re.findall(r'[aeiouy]+', word))
            if word.endswith('e') and not word.endswith('le') and syllable_count > 1:
                syllable_count -= 1
            return max(1, syllable_count)

        num_syllables = sum(count_syllables(w) for w in words)

        # Flesch Reading Ease Formula
        fre = 206.835 - (1.015 * (num_words / num_sentences)) - (84.6 * (num_syllables / num_words))
        fre = max(0.0, min(100.0, round(fre, 1)))

        # Flesch-Kincaid Grade Level Formula
        fkgl = (0.39 * (num_words / num_sentences)) + (11.8 * (num_syllables / num_words)) - 15.59
        grade_est = max(6, min(12, int(round(fkgl))))

        if fre >= 80:
            ease_label = "Very Easy (Middle School)"
        elif fre >= 60:
            ease_label = "Standard (High School)"
        elif fre >= 40:
            ease_label = "Fairly Difficult (Senior Secondary)"
        else:
            ease_label = "Advanced Academic"

        return {
            "flesch_reading_ease": fre,
            "grade_level": grade_est,
            "ease_label": ease_label
        }

    @staticmethod
    def _compute_pedagogical_score(title: str, description: str, text: str) -> int:
        score = 70
        full = f"{title} {description} {text}".lower()

        # Pedagogical boosters
        pedagogical_cues = ["explained", "how to", "step-by-step", "concept", "example", "formula", "proof", "derivation", "practice", "fundamentals", "overview"]
        for cue in pedagogical_cues:
            if cue in full:
                score += 4

        # Clickbait / Entertainment penalties
        clickbait_penalties = ["shocking", "you won't believe", "insane prank", "gone wrong", "exposed", "reacting to", "viral"]
        for pen in clickbait_penalties:
            if pen in full:
                score -= 20

        return max(50, min(100, score))

    @staticmethod
    def _extract_top_keywords(text: str) -> List[str]:
        words = re.findall(r'\b[a-z]{4,}\b', text)
        stop_words = {"this", "that", "with", "from", "have", "more", "your", "what", "which", "there", "about"}
        filtered = [w for w in words if w not in stop_words]
        return list(dict.fromkeys(filtered))[:8]
