"""
AI Token Quota & Multi-Tier Daily Cost Budgeting Engine.
Protects student, school, and platform infrastructure with atomic Redis rate limiting
and two-phase reservation & actual usage reconciliation.
"""

import json
import uuid
import datetime
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.redis_client import redis_client

logger = logging.getLogger("edufeedia.ai_budget")


class ModelPricingRegistry:
    """
    Dynamic pricing table and cost calculation across AI LLM providers and models.
    """
    PRICING_TABLE: Dict[str, Dict[str, Any]] = {
        "gpt-4o-mini": {
            "provider": "OpenAI",
            "prompt_per_m": 0.15,
            "completion_per_m": 0.60,
            "currency": "USD"
        },
        "gpt-4o": {
            "provider": "OpenAI",
            "prompt_per_m": 2.50,
            "completion_per_m": 10.00,
            "currency": "USD"
        },
        "gemini-1.5-flash": {
            "provider": "Google",
            "prompt_per_m": 0.075,
            "completion_per_m": 0.30,
            "currency": "USD"
        },
        "claude-3-5-sonnet": {
            "provider": "Anthropic",
            "prompt_per_m": 3.00,
            "completion_per_m": 15.00,
            "currency": "USD"
        },
        "local-mock": {
            "provider": "Edufeedia",
            "prompt_per_m": 0.0,
            "completion_per_m": 0.0,
            "currency": "USD"
        }
    }

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        pricing = cls.PRICING_TABLE.get(model_name.lower()) or cls.PRICING_TABLE["gpt-4o-mini"]
        p_cost = (prompt_tokens / 1_000_000.0) * pricing["prompt_per_m"]
        c_cost = (completion_tokens / 1_000_000.0) * pricing["completion_per_m"]
        return round(p_cost + c_cost, 7)


class AIBudgetManager:
    """
    Multi-tier atomic token budgeting and reconciliation:
    1. Student Daily Ceiling (Default: 40,000 tokens)
    2. School Daily Ceiling (Default: 2,000,000 tokens)
    3. Platform Daily Ceiling (Default: 50,000,000 tokens)
    """
    DEFAULT_STUDENT_DAILY_LIMIT = 40000
    DEFAULT_SCHOOL_DAILY_LIMIT = 2000000
    DEFAULT_PLATFORM_DAILY_LIMIT = 50000000

    @classmethod
    def _get_utc_date_str(cls) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    @classmethod
    def _get_ttl_to_midnight_utc(cls) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        tomorrow = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return max(60, int((tomorrow - now).total_seconds()))

    @classmethod
    def reserve_budget(
        cls,
        student_id: str,
        school_id: Optional[str] = None,
        estimated_tokens: int = 300,
        student_limit: Optional[int] = None,
        school_limit: Optional[int] = None,
        platform_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: Atomically checks all 3 tiers and reserves estimated tokens.
        Raises HTTP 429 if any tier is exhausted.
        """
        date_str = cls._get_utc_date_str()
        ttl = cls._get_ttl_to_midnight_utc()
        resolved_school = school_id or "default_school"

        s_limit = student_limit or cls.DEFAULT_STUDENT_DAILY_LIMIT
        sc_limit = school_limit or cls.DEFAULT_SCHOOL_DAILY_LIMIT
        p_limit = platform_limit or cls.DEFAULT_PLATFORM_DAILY_LIMIT

        student_key = f"ai:usage:student:{student_id}:{date_str}"
        school_key = f"ai:usage:school:{resolved_school}:{date_str}"
        platform_key = f"ai:usage:platform:{date_str}"

        # 1. Inspect current usage
        cur_student = int(redis_client.get(student_key) or 0)
        cur_school = int(redis_client.get(school_key) or 0)
        cur_platform = int(redis_client.get(platform_key) or 0)

        # Check Student Tier
        if cur_student + estimated_tokens > s_limit:
            logger.warning(f"[AI BUDGET EXCEEDED] Student {student_id} reached daily limit ({s_limit}). Consumed: {cur_student}.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily student AI tutor token budget exceeded ({s_limit} tokens). Quota resets at 00:00 UTC."
            )

        # Check School Tier
        if cur_school + estimated_tokens > sc_limit:
            logger.warning(f"[AI BUDGET EXCEEDED] School {resolved_school} reached daily quota ({sc_limit}).")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="School-wide daily AI quota has been reached. Please contact your school administrator."
            )

        # Check Platform Tier
        if cur_platform + estimated_tokens > p_limit:
            logger.critical(f"[AI BUDGET EXCEEDED] Platform daily limit reached ({p_limit}).")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="System AI capacity is currently saturated. Please try again later."
            )

        # 2. Atomic Reservation across all 3 tiers
        redis_client.incrby(student_key, estimated_tokens, ttl_seconds=ttl)
        redis_client.incrby(school_key, estimated_tokens, ttl_seconds=ttl)
        redis_client.incrby(platform_key, estimated_tokens, ttl_seconds=ttl)

        res_id = str(uuid.uuid4())
        reservation_data = {
            "reservation_id": res_id,
            "student_id": student_id,
            "school_id": resolved_school,
            "reserved_tokens": estimated_tokens,
            "date_str": date_str
        }
        redis_client.setex(f"ai:reservation:{res_id}", 300, json.dumps(reservation_data))

        return reservation_data

    @classmethod
    def reconcile_budget(
        cls,
        reservation_id: str,
        student_id: str,
        school_id: Optional[str],
        actual_prompt_tokens: int,
        actual_completion_tokens: int,
        model_name: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Phase 2: Reconciles actual LLM usage against the reserved estimate.
        Refunds or supplements token counts across all 3 tiers.
        """
        date_str = cls._get_utc_date_str()
        resolved_school = school_id or "default_school"
        actual_total = actual_prompt_tokens + actual_completion_tokens

        student_key = f"ai:usage:student:{student_id}:{date_str}"
        school_key = f"ai:usage:school:{resolved_school}:{date_str}"
        platform_key = f"ai:usage:platform:{date_str}"

        # Retrieve reservation
        res_raw = redis_client.get(f"ai:reservation:{reservation_id}")
        reserved_tokens = 300
        if res_raw:
            try:
                res_data = json.loads(res_raw)
                reserved_tokens = res_data.get("reserved_tokens", 300)
            except Exception:
                pass
            redis_client.delete(f"ai:reservation:{reservation_id}")

        delta = actual_total - reserved_tokens
        if delta > 0:
            redis_client.incrby(student_key, delta)
            redis_client.incrby(school_key, delta)
            redis_client.incrby(platform_key, delta)
        elif delta < 0:
            redis_client.decrby(student_key, abs(delta))
            redis_client.decrby(school_key, abs(delta))
            redis_client.decrby(platform_key, abs(delta))

        # Calculate exact cost
        cost_usd = ModelPricingRegistry.calculate_cost(
            model_name=model_name,
            prompt_tokens=actual_prompt_tokens,
            completion_tokens=actual_completion_tokens
        )

        final_student_usage = int(redis_client.get(student_key) or actual_total)

        logger.info(
            f"[AI BUDGET RECONCILED] Student: {student_id} | Model: {model_name} | "
            f"Actual: {actual_total} tokens (Delta: {delta:+d}) | Total Today: {final_student_usage} | Cost: ${cost_usd}"
        )

        return {
            "is_allowed": True,
            "actual_prompt_tokens": actual_prompt_tokens,
            "actual_completion_tokens": actual_completion_tokens,
            "total_tokens_consumed": actual_total,
            "tokens_consumed_today": final_student_usage,
            "estimated_cost_usd": cost_usd,
            "model_used": model_name
        }

    @classmethod
    def refund_reservation(cls, reservation: Dict[str, Any]) -> None:
        """Rolls back reserved tokens if LLM call crashes or gets aborted."""
        student_id = reservation.get("student_id")
        school_id = reservation.get("school_id") or "default_school"
        reserved = reservation.get("reserved_tokens", 0)
        date_str = reservation.get("date_str") or cls._get_utc_date_str()

        if student_id and reserved > 0:
            redis_client.decrby(f"ai:usage:student:{student_id}:{date_str}", reserved)
            redis_client.decrby(f"ai:usage:school:{school_id}:{date_str}", reserved)
            redis_client.decrby(f"ai:usage:platform:{date_str}", reserved)

        res_id = reservation.get("reservation_id")
        if res_id:
            redis_client.delete(f"ai:reservation:{res_id}")
        logger.info(f"[AI BUDGET REFUNDED] Refunded {reserved} tokens for student {student_id}")
