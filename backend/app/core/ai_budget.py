"""
AI Token Quota & Daily Cost Budgeting Engine.
Protects school and platform infrastructure from runaway LLM expenses by tracking
per-student and per-school daily token consumption.
"""

import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

logger = logging.getLogger("edufeedia.ai_budget")


class AIBudgetManager:
    """
    Manages daily student token allowances and cost budgets.
    """
    DEFAULT_DAILY_STUDENT_TOKEN_LIMIT = 40000  # ~100 Socratic queries per day
    COST_PER_MILLION_PROMPT_TOKENS = 0.15      # USD (gpt-4o-mini tier)
    COST_PER_MILLION_COMPLETION_TOKENS = 0.60  # USD

    # In-memory daily tracker (synchronized with Redis in production)
    _daily_usage: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_day_key(cls) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    @classmethod
    def check_and_consume_budget(
        cls,
        student_id: str,
        prompt_tokens: int,
        estimated_completion_tokens: int = 400,
        token_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validates whether the student has remaining token quota for today.
        If under limit, reserves tokens and returns budget metadata; otherwise raises HTTP 429.
        """
        day_key = cls._get_day_key()
        limit = token_limit or cls.DEFAULT_DAILY_STUDENT_TOKEN_LIMIT
        req_tokens = prompt_tokens + estimated_completion_tokens

        student_record = cls._daily_usage.setdefault(day_key, {}).setdefault(student_id, {
            "tokens_consumed": 0,
            "queries_count": 0,
            "estimated_cost_usd": 0.0
        })

        if student_record["tokens_consumed"] + req_tokens > limit:
            logger.warning(
                f"[AI BUDGET EXCEEDED] Student {student_id} exceeded daily token limit ({limit}). "
                f"Consumed: {student_record['tokens_consumed']} tokens."
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily AI tutor usage limit reached ({limit} tokens). Your quota resets at 00:00 UTC."
            )

        student_record["tokens_consumed"] += req_tokens
        student_record["queries_count"] += 1
        
        # Calculate cost
        cost = (
            (prompt_tokens / 1_000_000.0) * cls.COST_PER_MILLION_PROMPT_TOKENS +
            (estimated_completion_tokens / 1_000_000.0) * cls.COST_PER_MILLION_COMPLETION_TOKENS
        )
        student_record["estimated_cost_usd"] += cost

        return {
            "is_allowed": True,
            "tokens_consumed_today": student_record["tokens_consumed"],
            "remaining_tokens": max(0, limit - student_record["tokens_consumed"]),
            "daily_limit": limit,
            "queries_today": student_record["queries_count"],
            "estimated_cost_today_usd": round(student_record["estimated_cost_usd"], 6)
        }

    @classmethod
    def get_student_daily_usage(cls, student_id: str) -> Dict[str, Any]:
        day_key = cls._get_day_key()
        record = cls._daily_usage.get(day_key, {}).get(student_id, {
            "tokens_consumed": 0,
            "queries_count": 0,
            "estimated_cost_usd": 0.0
        })
        limit = cls.DEFAULT_DAILY_STUDENT_TOKEN_LIMIT
        return {
            "student_id": student_id,
            "day": day_key,
            "tokens_consumed": record["tokens_consumed"],
            "daily_limit": limit,
            "remaining_tokens": max(0, limit - record["tokens_consumed"]),
            "queries_count": record["queries_count"],
            "estimated_cost_usd": round(record["estimated_cost_usd"], 6)
        }
