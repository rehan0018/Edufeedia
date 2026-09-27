"""
NCERT Curriculum & Textbook Ingestion & Search Adapter.
Provides authoritative textbook readings, chapter excerpts, and official learning outcomes
aligned to CBSE and National Curriculum Framework (NCF).
"""

from typing import List, Dict, Any, Optional

class NCERTSearchAdapter:
    """
    Finds verified NCERT textbook chapters, official curriculum readings,
    and foundational summaries for Class 6 through 12.
    """

    NCERT_CHAPTER_INDEX: List[Dict[str, Any]] = [
        {
            "id": "ncert-c8-sci-ch1",
            "title": "NCERT Class 8 Science: Crop Production & Plant Nutrition",
            "description": "Comprehensive reading from NCERT textbook detailing photosynthesis, autotrophic nutrition, stomatal mechanics, and plant energy synthesis.",
            "subject": "Biology",
            "topic": "Photosynthesis",
            "grade_level": 8,
            "board": "CBSE",
            "chapter": "Chapter 1: Nutrition in Plants",
            "source_url": "https://ncert.nic.in/textbook.php?hesc1=1-18",
            "read_time_minutes": 12,
            "excerpt": "Green plants make their own food by the process of photosynthesis. During photosynthesis, chlorophyll containing cells of leaves in the presence of sunlight use carbon dioxide and water to synthesize carbohydrates. Oxygen is released in the process.",
            "learning_outcomes": [
                "Understand the formula for photosynthesis: 6CO2 + 6H2O + light -> C6H12O6 + 6O2",
                "Explain the function of chlorophyll and stomata in gas exchange",
                "Identify raw materials and products of plant nutrition"
            ]
        },
        {
            "id": "ncert-c9-phy-ch9",
            "title": "NCERT Class 9 Science: Force and Laws of Motion",
            "description": "Official NCERT Chapter 9 reading exploring Newton's three laws of motion, inertia, momentum, and real-life action-reaction pairs.",
            "subject": "Physics",
            "topic": "Newton's Laws",
            "grade_level": 9,
            "board": "CBSE",
            "chapter": "Chapter 9: Force and Laws of Motion",
            "source_url": "https://ncert.nic.in/textbook.php?iesc1=9-15",
            "read_time_minutes": 15,
            "excerpt": "The third law of motion states that when one object exerts a force on another object, the second object instantaneously exerts a force back on the first. These two forces are always equal in magnitude but opposite in direction.",
            "learning_outcomes": [
                "State Newton's First, Second, and Third Laws of Motion",
                "Calculate force using mass and acceleration (F=ma)",
                "Identify action-reaction force pairs in swimming, walking, and rocket propulsion"
            ]
        },
        {
            "id": "ncert-c9-phy-ch10",
            "title": "NCERT Class 9 Science: Gravitation & Free Fall",
            "description": "Official NCERT Chapter 10 reading covering the Universal Law of Gravitation, Kepler's laws, acceleration due to gravity, and mass vs weight.",
            "subject": "Physics",
            "topic": "Gravity",
            "grade_level": 9,
            "board": "CBSE",
            "chapter": "Chapter 10: Gravitation",
            "source_url": "https://ncert.nic.in/textbook.php?iesc1=10-15",
            "read_time_minutes": 14,
            "excerpt": "Every object in the universe attracts every other object with a force which is proportional to the product of their masses and inversely proportional to the square of the distance between them.",
            "learning_outcomes": [
                "Differentiate between Universal Gravitational Constant G and local gravity g",
                "Understand the physics of tides and planetary orbits",
                "Solve numerical problems involving gravitational attraction"
            ]
        },
        {
            "id": "ncert-c10-math-ch4",
            "title": "NCERT Class 10 Mathematics: Quadratic Equations",
            "description": "Official NCERT Chapter 4 covering standard quadratic equations, solution by factorization, completing the square, and quadratic formula.",
            "subject": "Mathematics",
            "topic": "Quadratic Equations",
            "grade_level": 10,
            "board": "CBSE",
            "chapter": "Chapter 4: Quadratic Equations",
            "source_url": "https://ncert.nic.in/textbook.php?jemh1=4-15",
            "read_time_minutes": 16,
            "excerpt": "A quadratic equation in the variable x is an equation of the form ax^2 + bx + c = 0, where a, b, c are real numbers and a != 0. The roots can be determined using the discriminant D = b^2 - 4ac.",
            "learning_outcomes": [
                "Identify real and distinct, equal, or imaginary roots using discriminant",
                "Apply the quadratic formula to solve real-world distance and work problems",
                "Master factorisation by splitting the middle term"
            ]
        }
    ]

    @classmethod
    def search(
        cls,
        topic: str,
        grade_level: int,
        board: str = "CBSE",
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching NCERT chapters and official reading materials.
        """
        results = []
        topic_lower = topic.lower()

        for item in cls.NCERT_CHAPTER_INDEX:
            # Match on topic, grade proximity (+/- 1 grade allowed for prerequisites), and board
            is_topic_match = (
                item["topic"].lower() in topic_lower or
                topic_lower in item["topic"].lower() or
                any(w in item["title"].lower() for w in topic_lower.split())
            )
            is_grade_match = abs(item["grade_level"] - grade_level) <= 1

            if is_topic_match and is_grade_match:
                results.append(item)

        if not results:
            # If no exact topic match, find by subject and grade fallback
            for item in cls.NCERT_CHAPTER_INDEX:
                if subject and item["subject"].lower() == subject.lower() and item["grade_level"] == grade_level:
                    results.append(item)

        return results
