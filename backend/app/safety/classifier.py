import re
import math
from typing import Dict, List, Any

# Heuristic category signals with positive and negative weights for transformer-like text categorization
CATEGORY_SIGNALS = {
    "TOXICITY": {
        "cues": ["stupid", "idiot", "hate", "kill", "shut up", "ugly", "trash", "loser", "horrible", "destroy"],
        "base_weight": 0.05
    },
    "VIOLENCE": {
        "cues": ["explosive", "bomb", "kill", "murder", "assault", "gun", "knife", "blood", "attack", "weapon", "shoot", "grenade", "poison"],
        "base_weight": 0.08
    },
    "NSFW": {
        "cues": ["nude", "sex", "porn", "erotic", "nsfw", "xxx", "bikini", "adult content", "dating app"],
        "base_weight": 0.09
    },
    "DRUGS": {
        "cues": ["meth", "cocaine", "weed", "heroin", "vape", "ecstasy", "pills", "high on", "smoke joint", "alcohol binge"],
        "base_weight": 0.08
    },
    "DANGEROUS_ACTIVITIES": {
        "cues": ["challenge", "dare", "bleach", "stunt", "hack", "bypass", "exploit", "burn", "fire trick", "electrocute"],
        "base_weight": 0.07
    },
    "EDUCATIONAL_QUALITY": {
        "cues": [
            "formula", "equation", "theorem", "solve", "explain", "derive", "introduction", "process",
            "experiment", "ncert", "cbse", "curriculum", "concept", "algorithm", "biology", "physics",
            "chemistry", "mathematics", "functions", "cellular", "respiration", "quantum", "history", "lesson"
        ],
        "base_weight": 0.15
    }
}

class SafetyClassifier:
    """
    Multi-category content safety and educational quality classifier.
    Computes category confidence scores in [0.0, 1.0].
    """

    def predict(self, text: str) -> Dict[str, Dict[str, Any]]:
        if not text:
            return {}

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        total_words = max(1, len(words))

        results = {}

        # 1. Evaluate educational score
        edu_cues = CATEGORY_SIGNALS["EDUCATIONAL_QUALITY"]["cues"]
        edu_matches = sum(1 for cue in edu_cues if cue in text_lower)
        edu_density = min(1.0, (edu_matches * 0.25) + 0.10 if edu_matches > 0 else 0.05)
        results["EDUCATIONAL_QUALITY"] = {
            "score": round(edu_density, 3),
            "severity": "HIGH" if edu_density >= 0.7 else ("MEDIUM" if edu_density >= 0.3 else "LOW")
        }

        # 2. Evaluate risk categories
        risk_categories = ["TOXICITY", "VIOLENCE", "NSFW", "DRUGS", "DANGEROUS_ACTIVITIES"]
        for cat in risk_categories:
            cues = CATEGORY_SIGNALS[cat]["cues"]
            matched_cues = [cue for cue in cues if re.search(r'\b' + re.escape(cue) + r'\b', text_lower)]
            
            # Non-linear probability curve based on match density
            cue_count = len(matched_cues)
            if cue_count == 0:
                score = 0.01
            elif cue_count == 1:
                score = 0.65
            elif cue_count == 2:
                score = 0.85
            else:
                score = min(0.99, 0.85 + (cue_count * 0.05))

            severity = "HIGH" if score >= 0.80 else ("MEDIUM" if score >= 0.50 else "LOW")
            results[cat] = {
                "score": round(score, 3),
                "severity": severity,
                "matched_cues": matched_cues
            }

        return results

# Singleton instance
classifier_instance = SafetyClassifier()

def classify_text(text: str) -> Dict[str, Dict[str, Any]]:
    return classifier_instance.predict(text)
