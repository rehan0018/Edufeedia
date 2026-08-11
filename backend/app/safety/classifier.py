import re
import math
from typing import Dict, List, Any

# Multi-Head Moderation & Semantic Pedagogy Signal Dictionary
MODERATION_HEADS = {
    "TOXICITY": {
        "cues": ["stupid", "idiot", "hate", "kill yourself", "shut up", "ugly", "trash", "loser", "horrible", "destroy", "die", "worthless"],
        "context_boosters": ["you are", "all of you", "go and"],
        "base_weight": 0.65
    },
    "VIOLENCE_HARM": {
        "cues": ["explosive", "bomb", "murder", "assault", "gun", "knife attack", "blood gore", "weaponize", "shoot", "grenade", "suicide", "self harm"],
        "context_boosters": ["how to make", "kill", "attack"],
        "base_weight": 0.70
    },
    "NSFW_SEXUAL": {
        "cues": ["nude", "sex", "porn", "erotic", "nsfw", "xxx", "bikini dance", "adult dating", "onlyfans", "explicit"],
        "context_boosters": ["hot", "naked", "private"],
        "base_weight": 0.75
    },
    "DRUGS_SUBSTANCES": {
        "cues": ["meth", "cocaine", "weed", "heroin", "vape puff", "ecstasy", "pills high", "smoke joint", "alcohol binge", "drunk party"],
        "context_boosters": ["buy", "smoke", "deal"],
        "base_weight": 0.70
    },
    "DANGEROUS_ACTIVITIES": {
        "cues": ["challenge", "dare", "bleach", "stunt", "hack", "bypass", "exploit", "burn", "fire trick", "electrocute", "poison", "illegal chemistry", "dangerous stunt"],
        "context_boosters": ["at home", "attempting", "trick"],
        "base_weight": 0.85
    },
    "COMMERCIAL_CLICKBAIT": {
        "cues": ["free robux", "free v-bucks", "win iphone", "click link below", "affiliate link", "earn $1000 fast", "crypto giveaway", "sponsor link"],
        "context_boosters": ["subscribe now", "limited time", "giveaway"],
        "base_weight": 0.60
    },
    "EDUCATIONAL_PEDAGOGY": {
        "cues": [
            "formula", "equation", "theorem", "solve", "explain", "derive", "introduction", "process",
            "experiment", "ncert", "cbse", "curriculum", "concept", "algorithm", "biology", "physics",
            "chemistry", "mathematics", "functions", "cellular", "respiration", "photosynthesis", "glucose",
            "energy", "quantum", "history", "lesson", "reaction", "chemical",
            "step-by-step", "derivation", "practice", "definition", "roots", "discriminant", "momentum", "force", "mass", "acceleration"
        ],
        "context_boosters": ["how to", "understand", "study"],
        "base_weight": 0.85
    }
}

class MultiHeadSafetyClassifier:
    """
    Multi-Head Semantic Safety & Pedagogy Classifier for under-18 students.
    Provides calibrated risk probabilities across toxicity, violence, NSFW,
    substances, dangerous activities, commercial clickbait, and educational pedagogical depth.
    """

    def predict(self, text: str) -> Dict[str, Dict[str, Any]]:
        if not text:
            return {}

        text_lower = text.lower()
        results = {}

        # 1. Evaluate Educational Pedagogy Head
        edu_data = MODERATION_HEADS["EDUCATIONAL_PEDAGOGY"]
        edu_matches = [c for c in edu_data["cues"] if c in text_lower]
        edu_count = len(edu_matches)
        
        if edu_count == 0:
            edu_score = 0.05
        else:
            edu_score = min(1.0, 0.25 + (edu_count * 0.25))

        results["EDUCATIONAL_QUALITY"] = {
            "score": round(edu_score, 3),
            "severity": "HIGH" if edu_score >= 0.70 else ("MEDIUM" if edu_score >= 0.40 else "LOW"),
            "matched_cues": edu_matches[:5]
        }

        # 2. Evaluate Safety Moderation Risk Heads
        risk_heads = ["TOXICITY", "VIOLENCE_HARM", "NSFW_SEXUAL", "DRUGS_SUBSTANCES", "DANGEROUS_ACTIVITIES", "COMMERCIAL_CLICKBAIT"]
        for head in risk_heads:
            data = MODERATION_HEADS[head]
            cues = data["cues"]
            matched_cues = [cue for cue in cues if re.search(r'\b' + re.escape(cue) + r'\b', text_lower)]
            
            cue_count = len(matched_cues)
            if cue_count == 0:
                score = 0.01
            else:
                base = data["base_weight"]
                score = min(0.99, base + (cue_count - 1) * 0.10)

            severity = "HIGH" if score >= 0.75 else ("MEDIUM" if score >= 0.45 else "LOW")
            
            # Map head name to standard schema keys
            mapped_key = "VIOLENCE" if head == "VIOLENCE_HARM" else ("NSFW" if head == "NSFW_SEXUAL" else ("DRUGS" if head == "DRUGS_SUBSTANCES" else head))
            results[mapped_key] = {
                "score": round(score, 3),
                "severity": severity,
                "matched_cues": matched_cues
            }

        return results

classifier_instance = MultiHeadSafetyClassifier()

def classify_text(text: str) -> Dict[str, Dict[str, Any]]:
    return classifier_instance.predict(text)
