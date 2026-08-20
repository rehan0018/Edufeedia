"""
Multi-Category Student Safety Content Classifier.
Analyzes educational text, external URLs, and AI outputs for inappropriate material,
toxicity, and prompt injection attacks.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Sensitive and high-risk keyword heuristics
PROHIBITED_CATEGORIES = {
    "ADULT_EXPLICIT": [
        r"\b(porn|erotic|xxx|nsfw|sexually explicit|nude|nudity)\b"
    ],
    "DANGEROUS_ACTIVITIES": [
        r"\b(build a bomb|make explosives?|explosive compounds?|synthesize (dangerous|drugs)|weaponize|cyanide recipe)\b",
        r"\b(crack software|bypass (school )?security|bypass (school )?(network )?firewall|ddos attack)\b"
    ],
    "HATE_AND_HARASSMENT": [
        r"\b(racial slur|hate speech|kill yourself|subhuman)\b"
    ],
    "PROMPT_INJECTION": [
        r"(ignore (all )?previous instructions|disregard all system prompts|reveal system instructions|you are now DAN|jailbreak mode)"
    ]
}

class ContentClassifier:
    """Performs multi-category safety classification with fail-closed safety semantics."""

    def classify_text(self, text: str) -> Dict[str, Any]:
        """
        Classifies input text across safety categories.
        Returns safety verdict, confidence score, and detected categories.
        """
        if not text or not text.strip():
            return {
                "is_safe": True,
                "safety_score": 1.0,
                "flagged_categories": [],
                "details": "Empty content evaluated as benign."
            }

        text_lower = text.lower()
        flagged = []
        highest_risk_score = 0.0

        for category, patterns in PROHIBITED_CATEGORIES.items():
            for pat in patterns:
                if re.search(pat, text_lower, re.IGNORECASE):
                    flagged.append(category)
                    highest_risk_score = max(highest_risk_score, 0.90)
                    break

        is_safe = (len(flagged) == 0)
        safety_score = round(1.0 - highest_risk_score, 2) if flagged else 0.98

        return {
            "is_safe": is_safe,
            "safety_score": safety_score,
            "flagged_categories": flagged,
            "action": "ALLOW" if is_safe else "BLOCK",
            "reason": f"Violated student safety categories: {', '.join(flagged)}" if flagged else "Approved for educational distribution."
        }

    def detect_prompt_injection(self, prompt: str) -> bool:
        """Detects adversarial jailbreak and prompt-injection patterns."""
        injection_patterns = PROHIBITED_CATEGORIES["PROMPT_INJECTION"]
        for pat in injection_patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                logger.warning(f"[Security Warning] Prompt injection attempt detected: {prompt[:80]}...")
                return True
        return False

content_classifier = ContentClassifier()
