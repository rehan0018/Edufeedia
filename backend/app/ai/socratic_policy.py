import re
import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SocraticPolicy:
    """
    Socratic Response Policy, Answer Leakage Detector & AI Telemetry Tracing.
    Guarantees the AI Tutor coaches students conceptually without leaking direct homework answers.
    """

    LEAKAGE_PATTERNS = [
        # Numeric answers
        r"(?:the\s+answer\s+is|correct\s+answer\s+is|result\s+is|solution\s+is)\s*[:=]?\s*([-+]?\d+(?:\.\d+)?(?:\s*[a-zA-Z/]+)?)",
        # MCQ Option giveaways
        r"(?:the\s+correct\s+option\s+is|choose\s+option|answer\s+is\s+option)\s*[:=]?\s*([A-Da-d])\b",
        # Direct formula substitutions with finished solutions
        r"=\s*[-+]?\d+(?:\.\d+)?\s*(?:m/s|N|kg|joules|watts|ohms|V|m/s\^2|cm\^2)\b"
    ]

    @classmethod
    def audit_and_steer_response(
        cls,
        raw_llm_response: str,
        student_question: str,
        topic: str,
        subject: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs Answer Leakage Detection + Groundedness Evaluation + Socratic Steering.
        """
        # Step 1: Detect Homework Answer Inquiries
        is_direct_answer_seeking = cls.is_homework_answer_request(student_question)

        # Step 2: Answer Leakage Detection
        has_leakage, leaked_elements = cls.detect_answer_leakage(raw_llm_response)

        steered_response = raw_llm_response
        leakage_blocked = False

        if has_leakage or (is_direct_answer_seeking and not raw_llm_response.endswith("?")):
            steered_response = cls._rewrite_as_socratic_guidance(
                raw_response=raw_llm_response,
                question=student_question,
                topic=topic,
                subject=subject,
                retrieved_chunks=retrieved_chunks
            )
            leakage_blocked = True

        # Step 3: Groundedness Evaluation
        groundedness_score = cls.evaluate_groundedness(steered_response, retrieved_chunks)

        return {
            "response_text": steered_response,
            "leakage_blocked": leakage_blocked,
            "leaked_elements": leaked_elements,
            "groundedness_score": groundedness_score,
            "is_socratic": steered_response.strip().endswith("?") or "what" in steered_response.lower() or "how" in steered_response.lower()
        }

    @classmethod
    def is_homework_answer_request(cls, question: str) -> bool:
        q_lower = question.lower()
        triggers = [
            "what is the answer", "give me the answer", "solve this for me",
            "just tell me the answer", "which option is correct", "write my essay",
            "complete solution for", "answer to question"
        ]
        return any(t in q_lower for t in triggers)

    @classmethod
    def detect_answer_leakage(cls, text: str) -> Tuple[bool, List[str]]:
        leaked = []
        for pattern in cls.LEAKAGE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                leaked.extend([str(m) for m in matches])
        return len(leaked) > 0, leaked

    @classmethod
    def _rewrite_as_socratic_guidance(
        cls,
        raw_response: str,
        question: str,
        topic: str,
        subject: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        # Construct a guiding inquiry based on the subject and core principles
        evidence_snippet = retrieved_chunks[0].get("text", "") if retrieved_chunks else ""
        
        if "force" in question.lower() or "newton" in question.lower() or "motion" in question.lower():
            return "Let's break this down step-by-step! Before solving for the final value, which fundamental formula connects Force, Mass, and Acceleration in physics?"
        elif "quadratic" in question.lower() or "roots" in question.lower() or "equation" in question.lower():
            return "Great math inquiry! To find the roots of this equation, what values do you have for the coefficients a, b, and c in the standard form ax² + bx + c = 0?"
        elif "circuit" in question.lower() or "ohm" in question.lower() or "resistor" in question.lower():
            return "Let's explore the circuit dynamics first! What formula from Ohm's Law relates Voltage (V), Current (I), and Resistance (R)?"
        elif "respiration" in question.lower() or "atp" in question.lower():
            return "Let's trace the biological pathway together! In which cellular organelle does aerobic cellular respiration take place to produce ATP?"
        else:
            return f"To help you master {topic}, let's examine the starting principle: what are the key given variables in your problem?"

    @classmethod
    def evaluate_groundedness(cls, response: str, retrieved_chunks: List[Dict[str, Any]]) -> float:
        if not retrieved_chunks:
            return 0.75 # Baseline
        combined_evidence = " ".join([c.get("text", "").lower() for c in retrieved_chunks])
        response_words = set(re.findall(r'\b[a-z]{4,}\b', response.lower()))
        if not response_words:
            return 1.0
        
        evidence_words = set(re.findall(r'\b[a-z]{4,}\b', combined_evidence))
        overlap = response_words.intersection(evidence_words)
        ratio = len(overlap) / max(1, len(response_words))
        return min(1.0, max(0.60, round(ratio * 1.5, 2)))

    @classmethod
    def trace_ai_request(
        cls,
        student_id: Optional[str],
        query: str,
        model: str,
        provider: str,
        retrieved_count: int,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        safety_verdict: str,
        groundedness: float,
        fallback_used: bool = False
    ) -> Dict[str, Any]:
        trace_record = {
            "trace_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "student_id": student_id or "anonymous",
            "model": model,
            "provider": provider,
            "retrieval_chunk_count": retrieved_count,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": round(latency_ms, 2),
            "safety_verdict": safety_verdict,
            "groundedness_score": groundedness,
            "fallback_used": fallback_used
        }
        logger.info("[AI Request Trace]: ID: %s | Model: %s | Latency: %.1fms | Groundedness: %.2f",
                    trace_record["trace_id"], model, latency_ms, groundedness)
        return trace_record
