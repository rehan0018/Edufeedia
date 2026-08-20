import re
from typing import Dict, Any

class PromptInjectionDetector:
    """
    Evaluates student prompts and retrieved contexts for adversarial injection,
    jailbreak attempts (DAN mode), and instruction overriding.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(safety|prior|system)\s+protocols",
        r"you\s+are\s+now\s+(in\s+)?DAN(\s+mode)?",
        r"do\s+anything\s+now",
        r"system\s+prompt\s+override",
        r"reveal\s+(the\s+)?system\s+instructions",
        r"forget\s+(your\s+)?prior\s+ethical",
        r"print\s+(the\s+)?database\s+credentials",
        r"unrestricted\s+administrator"
    ]

    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    @classmethod
    def analyze_prompt(cls, prompt: str) -> Dict[str, Any]:
        if not prompt:
            return {"is_injection_detected": False, "risk_score": 0.0, "matched_patterns": []}

        matched = []
        for pat in cls.COMPILED_PATTERNS:
            if pat.search(prompt):
                matched.append(pat.pattern)

        is_detected = len(matched) > 0
        risk_score = 0.95 if is_detected else 0.05

        return {
            "is_injection_detected": is_detected,
            "risk_score": risk_score,
            "matched_patterns": matched
        }
