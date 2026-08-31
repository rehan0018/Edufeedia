import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PromptInjectionDetector:
    """
    Authoritative detection and sanitization engine for student prompts and retrieved contexts.
    Detects adversarial injection, jailbreak attempts (DAN mode), safety protocol disabling,
    and instruction overriding.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above|system|\s+)*instructions",
        r"disregard\s+(all\s+)?(safety|prior|system|ethical|\s+)*(protocols|guidelines|rules)?",
        r"(you\s+are\s+now\s+in\s+)?developer\s+mode",
        r"do\s+anything\s+now",
        r"\bjailbreak\b",
        r"system\s+(prompt\s+)?override",
        r"reveal\s+(the\s+)?(hidden\s+)?system\s+(prompt|instructions)",
        r"print\s+(the\s+)?(database\s+credentials|secret_key)",
        r"\bsecret_key\b",
        r"act\s+as\s+an\s+unrestricted\s+(assistant|administrator|ai)",
        r"forget\s+(your\s+)?prior\s+(ethical|safety)",
        r"disable\s+safety.*",
        r"override\s+moderation"
    ]

    COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    @classmethod
    def analyze_prompt(cls, prompt: str) -> Dict[str, Any]:
        """Performs deep regex inspection of prompt text."""
        if not prompt or not prompt.strip():
            return {"is_injection_detected": False, "risk_score": 0.0, "matched_patterns": []}

        matched = []
        for pat in cls.COMPILED_PATTERNS:
            if pat.search(prompt):
                matched.append(pat.pattern)

        is_detected = len(matched) > 0
        risk_score = 0.95 if is_detected else 0.05

        if is_detected:
            logger.warning(f"[Security Warning] Prompt injection attempt detected: {prompt[:80]}...")

        return {
            "is_injection_detected": is_detected,
            "risk_score": risk_score,
            "matched_patterns": matched
        }

    @classmethod
    def detect(cls, prompt: str) -> bool:
        """Boolean helper returning True if prompt contains injection patterns."""
        return cls.analyze_prompt(prompt)["is_injection_detected"]

    @classmethod
    def sanitize_prompt(cls, prompt: str) -> str:
        """Sanitizes adversarial instructions into safe curriculum inquiry markers."""
        if not prompt:
            return ""
        clean = prompt
        for pat in cls.COMPILED_PATTERNS:
            clean = pat.sub("[redacted curriculum inquiry]", clean)
        return clean.strip()

prompt_injection_detector = PromptInjectionDetector()
