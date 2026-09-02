"""
AI Token Quota & Multi-Tier Daily Cost Budgeting Engine.
Protects student, school, and platform infrastructure with atomic Redis Lua scripts
and two-phase active reservation & actual usage reconciliation.
"""

import json
import uuid
import datetime
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.redis_client import redis_client

logger = logging.getLogger("edufeedia.ai_budget")


class ModelPricingTable:
    """
    Authoritative pricing table and cost calculation across AI LLM providers and models.
    Fails closed on unknown models to prevent unmetered/under-metered billing drift.
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
    def get_pricing(cls, model_name: str) -> Dict[str, Any]:
        """Retrieves model pricing strictly. Raises HTTPException if unknown."""
        key = (model_name or "").lower().strip()
        if key not in cls.PRICING_TABLE:
            logger.error(f"[AI PRICING ERROR] Unknown model requested: '{model_name}'. Failing closed.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model pricing is unconfigured for '{model_name}'. Inferences with unpriced models are blocked."
            )
        return cls.PRICING_TABLE[key]

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        pricing = cls.get_pricing(model_name)
        p_cost = (prompt_tokens / 1_000_000.0) * pricing["prompt_per_m"]
        c_cost = (completion_tokens / 1_000_000.0) * pricing["completion_per_m"]
        return round(p_cost + c_cost, 7)


# Backwards compatibility alias
ModelPricingRegistry = ModelPricingTable


RESERVE_BUDGET_LUA = """
local tokens = tonumber(ARGV[1])
local s_limit = tonumber(ARGV[2])
local sc_limit = tonumber(ARGV[3])
local p_limit = tonumber(ARGV[4])
local day_ttl = tonumber(ARGV[5])
local res_ttl = tonumber(ARGV[6])

-- 1. Student Check
local s_used = tonumber(redis.call('get', KEYS[1]) or '0')
local s_res = tonumber(redis.call('get', KEYS[4]) or '0')
if (s_used + s_res + tokens) > s_limit then
    return {'ERR_STUDENT_LIMIT', tostring(s_used + s_res), tostring(s_limit)}
end

-- 2. School Check (if tenant-scoped)
if KEYS[2] ~= 'NONE' and KEYS[2] ~= '' then
    local sc_used = tonumber(redis.call('get', KEYS[2]) or '0')
    local sc_res = tonumber(redis.call('get', KEYS[5]) or '0')
    if (sc_used + sc_res + tokens) > sc_limit then
        return {'ERR_SCHOOL_LIMIT', tostring(sc_used + sc_res), tostring(sc_limit)}
    end
end

-- 3. Platform Check
local p_used = tonumber(redis.call('get', KEYS[3]) or '0')
local p_res = tonumber(redis.call('get', KEYS[6]) or '0')
if (p_used + p_res + tokens) > p_limit then
    return {'ERR_PLATFORM_LIMIT', tostring(p_used + p_res), tostring(p_limit)}
end

-- 4. Atomically commit active reservations
redis.call('incrby', KEYS[4], tokens)
redis.call('expire', KEYS[4], day_ttl)

if KEYS[2] ~= 'NONE' and KEYS[2] ~= '' then
    redis.call('incrby', KEYS[5], tokens)
    redis.call('expire', KEYS[5], day_ttl)
end

redis.call('incrby', KEYS[6], tokens)
redis.call('expire', KEYS[6], day_ttl)

-- Store reservation metadata record
redis.call('set', KEYS[7], ARGV[7], 'EX', res_ttl)

return {'OK', tostring(tokens), tostring(s_used + s_res + tokens)}
"""

RECONCILE_BUDGET_LUA = """
local actual = tonumber(ARGV[1])
local day_ttl = tonumber(ARGV[2])
local reserved_fallback = tonumber(ARGV[3])

-- Retrieve reservation amount
local reserved = reserved_fallback
local res_raw = redis.call('get', KEYS[7])
if res_raw then
    redis.call('del', KEYS[7])
end

-- Release active reservation
redis.call('decrby', KEYS[4], reserved)
if KEYS[2] ~= 'NONE' and KEYS[2] ~= '' then
    redis.call('decrby', KEYS[5], reserved)
end
redis.call('decrby', KEYS[6], reserved)

-- Commit actual usage to permanent daily counters
local s_final = redis.call('incrby', KEYS[1], actual)
redis.call('expire', KEYS[1], day_ttl)

if KEYS[2] ~= 'NONE' and KEYS[2] ~= '' then
    redis.call('incrby', KEYS[2], actual)
    redis.call('expire', KEYS[2], day_ttl)
end

local p_final = redis.call('incrby', KEYS[3], actual)
redis.call('expire', KEYS[3], day_ttl)

return {'OK', tostring(actual), tostring(s_final)}
"""

REFUND_BUDGET_LUA = """
local reserved = tonumber(ARGV[1])
local res_raw = redis.call('get', KEYS[4])
if res_raw then
    redis.call('del', KEYS[4])
end

redis.call('decrby', KEYS[1], reserved)
if KEYS[2] ~= 'NONE' and KEYS[2] ~= '' then
    redis.call('decrby', KEYS[2], reserved)
end
redis.call('decrby', KEYS[3], reserved)

return {'OK', tostring(reserved)}
"""


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
        Phase 1: Atomically checks all 3 tiers via Redis Lua script and registers active reservation.
        Prevents phantom overcharges on crash and prevents race conditions across instances.
        """
        date_str = cls._get_utc_date_str()
        day_ttl = cls._get_ttl_to_midnight_utc()
        res_ttl = 300  # 5 minutes active reservation TTL

        s_limit = student_limit or cls.DEFAULT_STUDENT_DAILY_LIMIT
        sc_limit = school_limit or cls.DEFAULT_SCHOOL_DAILY_LIMIT
        p_limit = platform_limit or cls.DEFAULT_PLATFORM_DAILY_LIMIT

        student_usage_key = f"ai:usage:student:{student_id}:{date_str}"
        school_usage_key = f"ai:usage:school:{school_id}:{date_str}" if school_id else "NONE"
        platform_usage_key = f"ai:usage:platform:{date_str}"

        student_res_key = f"ai:active_res:student:{student_id}:{date_str}"
        school_res_key = f"ai:active_res:school:{school_id}:{date_str}" if school_id else "NONE"
        platform_res_key = f"ai:active_res:platform:{date_str}"

        res_id = str(uuid.uuid4())
        res_id_key = f"ai:reservation:{res_id}"

        reservation_data = {
            "reservation_id": res_id,
            "student_id": student_id,
            "school_id": school_id,
            "reserved_tokens": estimated_tokens,
            "date_str": date_str
        }

        keys = [
            student_usage_key,
            school_usage_key,
            platform_usage_key,
            student_res_key,
            school_res_key,
            platform_res_key,
            res_id_key
        ]

        args = [
            estimated_tokens,
            s_limit,
            sc_limit,
            p_limit,
            day_ttl,
            res_ttl,
            json.dumps(reservation_data)
        ]

        result = redis_client.eval_lua(RESERVE_BUDGET_LUA, keys, args)
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            status_code = result[0]
            if status_code == "ERR_STUDENT_LIMIT":
                cur = result[1]
                logger.warning(f"[AI BUDGET EXCEEDED] Student {student_id} reached daily limit ({s_limit}). Consumed/In-Flight: {cur}.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily student AI tutor token budget exceeded ({s_limit} tokens). Quota resets at 00:00 UTC."
                )
            elif status_code == "ERR_SCHOOL_LIMIT":
                logger.warning(f"[AI BUDGET EXCEEDED] School {school_id} reached daily quota ({sc_limit}).")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="School-wide daily AI quota has been reached. Please contact your school administrator."
                )
            elif status_code == "ERR_PLATFORM_LIMIT":
                logger.critical(f"[AI BUDGET EXCEEDED] Platform daily limit reached ({p_limit}).")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="System AI capacity is currently saturated. Please try again later."
                )

        return reservation_data

    @classmethod
    def reconcile_budget(
        cls,
        reservation_id: str,
        student_id: str,
        school_id: Optional[str],
        actual_prompt_tokens: int,
        actual_completion_tokens: int,
        model_name: str = "gpt-4o-mini",
        request_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Phase 2: Reconciles actual LLM usage against the active reservation in Redis,
        commits exact token count, and writes persistent financial AIUsageEvent to DB.
        """
        date_str = cls._get_utc_date_str()
        day_ttl = cls._get_ttl_to_midnight_utc()
        actual_total = actual_prompt_tokens + actual_completion_tokens

        student_usage_key = f"ai:usage:student:{student_id}:{date_str}"
        school_usage_key = f"ai:usage:school:{school_id}:{date_str}" if school_id else "NONE"
        platform_usage_key = f"ai:usage:platform:{date_str}"

        student_res_key = f"ai:active_res:student:{student_id}:{date_str}"
        school_res_key = f"ai:active_res:school:{school_id}:{date_str}" if school_id else "NONE"
        platform_res_key = f"ai:active_res:platform:{date_str}"

        res_id_key = f"ai:reservation:{reservation_id}"

        # Fetch reservation details
        res_raw = redis_client.get(res_id_key)
        reserved_tokens = 300
        if res_raw:
            try:
                res_data = json.loads(res_raw)
                reserved_tokens = res_data.get("reserved_tokens", 300)
            except Exception:
                pass

        keys = [
            student_usage_key,
            school_usage_key,
            platform_usage_key,
            student_res_key,
            school_res_key,
            platform_res_key,
            res_id_key
        ]

        args = [
            actual_total,
            day_ttl,
            reserved_tokens
        ]

        redis_client.eval_lua(RECONCILE_BUDGET_LUA, keys, args)

        # Exact financial cost calculation via strict pricing table
        pricing_info = ModelPricingTable.get_pricing(model_name)
        cost_usd = ModelPricingTable.calculate_cost(
            model_name=model_name,
            prompt_tokens=actual_prompt_tokens,
            completion_tokens=actual_completion_tokens
        )

        final_student_usage = int(redis_client.get(student_usage_key) or actual_total)

        # Persist financial and telemetry audit event to database
        if db:
            try:
                from app.models.models import AIUsageEvent
                usage_event = AIUsageEvent(
                    student_id=student_id,
                    school_id=school_id,
                    request_id=request_id,
                    reservation_id=reservation_id,
                    model=model_name,
                    provider=pricing_info["provider"],
                    prompt_tokens=actual_prompt_tokens,
                    completion_tokens=actual_completion_tokens,
                    total_tokens=actual_total,
                    cost_usd=cost_usd,
                    status="SUCCESS"
                )
                db.add(usage_event)
                db.commit()
            except Exception as e:
                logger.error(f"[AI USAGE EVENT PERSIST ERROR]: {e}", exc_info=True)

        logger.info(
            f"[AI BUDGET RECONCILED] Student: {student_id} | School: {school_id or 'Independent'} | "
            f"Model: {model_name} | Tokens: {actual_total} (Prompt: {actual_prompt_tokens}, Comp: {actual_completion_tokens}) | "
            f"Cost: ${cost_usd:.6f} {pricing_info['currency']} | Day Total: {final_student_usage}"
        )

        return {
            "is_allowed": True,
            "actual_prompt_tokens": actual_prompt_tokens,
            "actual_completion_tokens": actual_completion_tokens,
            "total_tokens_consumed": actual_total,
            "tokens_consumed_today": final_student_usage,
            "estimated_cost_usd": cost_usd,
            "model_used": model_name,
            "provider": pricing_info["provider"],
            "currency": pricing_info["currency"]
        }

    @classmethod
    def refund_reservation(cls, reservation: Dict[str, Any]) -> None:
        """Rolls back reserved tokens atomically if LLM call crashes or gets aborted."""
        student_id = reservation.get("student_id")
        school_id = reservation.get("school_id")
        reserved = reservation.get("reserved_tokens", 0)
        date_str = reservation.get("date_str") or cls._get_utc_date_str()
        res_id = reservation.get("reservation_id")

        if student_id and reserved > 0:
            student_res_key = f"ai:active_res:student:{student_id}:{date_str}"
            school_res_key = f"ai:active_res:school:{school_id}:{date_str}" if school_id else "NONE"
            platform_res_key = f"ai:active_res:platform:{date_str}"
            res_id_key = f"ai:reservation:{res_id}" if res_id else "NONE"

            keys = [
                student_res_key,
                school_res_key,
                platform_res_key,
                res_id_key
            ]
            args = [reserved]
            redis_client.eval_lua(REFUND_BUDGET_LUA, keys, args)

        logger.info(f"[AI BUDGET REFUNDED] Released active reservation of {reserved} tokens for student {student_id}")
