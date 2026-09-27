"""
Open Educational Resources (OER) & Interactive Simulations Search Adapter.
Discovers interactive HTML5 simulations (PhET Colorado), Khan Academy modules,
and open-licensed STEM activities.
"""

from typing import List, Dict, Any, Optional

class OERSearchAdapter:
    """
    Search adapter for PhET Interactive Simulations and Khan Academy verified modules.
    """

    OER_SIMULATION_INDEX: List[Dict[str, Any]] = [
        {
            "id": "phet-sim-photosynthesis",
            "title": "PhET: Photosynthesis & Light Absorption Studio",
            "description": "Interactive HTML5 laboratory simulation allowing students to manipulate light wavelength, water concentration, and carbon dioxide to observe glucose and oxygen synthesis in real-time.",
            "source_name": "PhET Interactive Simulations",
            "source_platform": "PhET",
            "resource_type": "interactive_sim",
            "subject": "Biology",
            "topic": "Photosynthesis",
            "grade_level": 8,
            "board": "CBSE",
            "source_url": "https://phet.colorado.edu/en/simulations/photosynthesis",
            "embed_url": "https://phet.colorado.edu/sims/html/molecules-and-light/latest/molecules-and-light_en.html",
            "duration_minutes": 10,
            "interactivity_type": "simulation_experiment",
            "license": "CC-BY 4.0",
            "learning_gain_potential": 0.94
        },
        {
            "id": "phet-sim-forces-motion",
            "title": "PhET: Forces and Motion Basics (Newton's Laws)",
            "description": "Experiment with friction, net force, mass, and velocity. See vectors and observe equal and opposite reactions in a tug-of-war and motion cart lab.",
            "source_name": "PhET Interactive Simulations",
            "source_platform": "PhET",
            "resource_type": "interactive_sim",
            "subject": "Physics",
            "topic": "Newton's Laws",
            "grade_level": 9,
            "board": "CBSE",
            "source_url": "https://phet.colorado.edu/en/simulations/forces-and-motion-basics",
            "embed_url": "https://phet.colorado.edu/sims/html/forces-and-motion-basics/latest/forces-and-motion-basics_en.html",
            "duration_minutes": 12,
            "interactivity_type": "simulation_experiment",
            "license": "CC-BY 4.0",
            "learning_gain_potential": 0.96
        },
        {
            "id": "phet-sim-gravity-orbits",
            "title": "PhET: Gravity and Planetary Orbits Laboratory",
            "description": "Visualize gravitational pull between Sun, Earth, Moon, and Space Station. Change mass and distance to test Kepler's laws and orbit stability.",
            "source_name": "PhET Interactive Simulations",
            "source_platform": "PhET",
            "resource_type": "interactive_sim",
            "subject": "Physics",
            "topic": "Gravity",
            "grade_level": 9,
            "board": "CBSE",
            "source_url": "https://phet.colorado.edu/en/simulations/gravity-and-orbits",
            "embed_url": "https://phet.colorado.edu/sims/html/gravity-and-orbits/latest/gravity-and-orbits_en.html",
            "duration_minutes": 10,
            "interactivity_type": "simulation_experiment",
            "license": "CC-BY 4.0",
            "learning_gain_potential": 0.95
        },
        {
            "id": "khan-module-photosynthesis",
            "title": "Khan Academy: Light Reactions and Chloroplast Mechanics",
            "description": "Deep-dive structured lesson with step-by-step diagrams detailing thylakoid membrane reactions, ATP synthesis, and carbon fixation.",
            "source_name": "Khan Academy",
            "source_platform": "Khan Academy",
            "resource_type": "reading",
            "subject": "Biology",
            "topic": "Photosynthesis",
            "grade_level": 8,
            "board": "CBSE",
            "source_url": "https://www.khanacademy.org/science/biology/photosynthesis-in-plants",
            "embed_url": None,
            "duration_minutes": 8,
            "interactivity_type": "guided_reading",
            "license": "Non-commercial Educational",
            "learning_gain_potential": 0.91
        },
        {
            "id": "khan-module-newtons-third-law",
            "title": "Khan Academy: Action-Reaction Pairs & Normal Forces",
            "description": "Clear conceptual breakdown explaining why equal and opposite forces never cancel each other out because they act on different bodies.",
            "source_name": "Khan Academy",
            "source_platform": "Khan Academy",
            "resource_type": "reading",
            "subject": "Physics",
            "topic": "Newton's Laws",
            "grade_level": 9,
            "board": "CBSE",
            "source_url": "https://www.khanacademy.org/science/physics/forces-newtons-laws/newtons-laws-of-motion",
            "embed_url": None,
            "duration_minutes": 9,
            "interactivity_type": "guided_reading",
            "license": "Non-commercial Educational",
            "learning_gain_potential": 0.92
        }
    ]

    @classmethod
    def search(
        cls,
        topic: str,
        grade_level: int,
        preferred_format: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching simulations and interactive learning resources.
        """
        results = []
        topic_lower = topic.lower()

        for item in cls.OER_SIMULATION_INDEX:
            is_topic_match = (
                item["topic"].lower() in topic_lower or
                topic_lower in item["topic"].lower() or
                any(w in item["title"].lower() for w in topic_lower.split())
            )
            is_grade_match = abs(item["grade_level"] - grade_level) <= 2

            if is_topic_match and is_grade_match:
                if preferred_format and item["resource_type"] != preferred_format and preferred_format in ["interactive_sim", "reading"]:
                    # Still keep it for diversity, but sort preferred first
                    results.append(item)
                else:
                    results.insert(0, item)

        return results
