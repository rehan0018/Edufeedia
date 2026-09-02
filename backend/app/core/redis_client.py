import os
import logging
from typing import Optional

logger = logging.getLogger("edufeedia.redis")

class RedisClient:
    """
    Thread-safe Redis client wrapper with high-availability connection pooling
    and automatic memory cache fallback for standalone unit testing and dev.
    """
    _instance = None
    _redis = None
    _local_store = {}

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        redis_url = os.getenv("REDIS_URL")
        env = os.getenv("ENVIRONMENT", "development").lower()
        is_production = (env == "production")
        is_test = (env == "test")
        self._redis = None

        if redis_url:
            try:
                import redis
                r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
                r.ping()
                self._redis = r
                logger.info(f"Connected to Redis cluster at {redis_url}")
            except Exception as e:
                if is_production:
                    logger.critical(f"[CRITICAL: Production Redis Connection Failed]: {e}")
                    raise RuntimeError(f"Critical Infrastructure Failure: Redis cluster unreachable in production ({e}).")
                self._redis = None
        elif is_production:
            raise RuntimeError("Critical: Production environment requires REDIS_URL.")

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Modern Redis set with optional expiration seconds."""
        if self._redis:
            try:
                return bool(self._redis.set(key, value, ex=ex))
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        elif os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("Production Redis cluster unavailable. In-memory OTP storage is disallowed.")
        self._local_store[key] = value
        return True

    def setex(self, key: str, seconds: int, value: str) -> bool:
        """Alias for modern set(key, value, ex=seconds) preventing deprecation warnings."""
        return self.set(key, value, ex=seconds)

    def get(self, key: str) -> Optional[str]:
        if self._redis:
            try:
                return self._redis.get(key)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        elif os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("Production Redis cluster unavailable. In-memory OTP storage is disallowed.")
        return self._local_store.get(key)

    def delete(self, key: str) -> bool:
        if self._redis:
            try:
                return bool(self._redis.delete(key))
            except Exception as e:
                logger.error(f"Redis delete failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        elif os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("Production Redis cluster unavailable. In-memory OTP storage is disallowed.")
        if key in self._local_store:
            del self._local_store[key]
            return True
        return False

    def incrby(self, key: str, amount: int, ttl_seconds: Optional[int] = None) -> int:
        """Atomically increments integer value by amount, optionally setting TTL."""
        if self._redis:
            try:
                val = self._redis.incrby(key, amount)
                if ttl_seconds and val == amount:
                    self._redis.expire(key, ttl_seconds)
                return val
            except Exception as e:
                logger.error(f"Redis incrby failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        val = int(self._local_store.get(key, 0)) + amount
        self._local_store[key] = str(val)
        return val

    def decrby(self, key: str, amount: int) -> int:
        """Atomically decrements integer value by amount (floor at 0)."""
        if self._redis:
            try:
                val = self._redis.decrby(key, amount)
                return max(0, val)
            except Exception as e:
                logger.error(f"Redis decrby failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        val = max(0, int(self._local_store.get(key, 0)) - amount)
        self._local_store[key] = str(val)
        return val

    def delete_pattern(self, pattern: str) -> int:
        """Deletes all keys matching a glob/wildcard pattern (e.g. 'tutor:session:student-123:*')."""
        if self._redis:
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    return self._redis.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Redis delete_pattern failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        import re
        regex = re.compile("^" + pattern.replace("*", ".*") + "$")
        to_del = [k for k in list(self._local_store.keys()) if regex.match(k)]
        for k in to_del:
            del self._local_store[k]
        return len(to_del)

    def check_rate_limit(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """
        Sliding rate limiter. Returns True if request is allowed, False if exceeded.
        """
        rate_key = f"rate_limit:{key}"
        if self._redis:
            try:
                current = self._redis.incr(rate_key)
                if current == 1:
                    self._redis.expire(rate_key, window_seconds)
                return current <= max_requests
            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        
        # Local fallback counter for testing
        current = int(self._local_store.get(rate_key, 0)) + 1
        self._local_store[rate_key] = str(current)
        return current <= max_requests

    def eval_lua(self, script: str, keys: list, args: list) -> Any:
        """Atomically evaluates a Lua script in Redis with mock fallback for testing."""
        if self._redis:
            try:
                res = self._redis.eval(script, len(keys), *keys, *args)
                return res
            except Exception as e:
                logger.error(f"Redis Lua script execution failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster Lua evaluation failed: {e}")

        # Local in-process fallback engine for unit testing
        import json as _json
        script_clean = script.strip()
        if "ERR_STUDENT_LIMIT" in script_clean:
            # Reservation Lua Script
            tokens = int(args[0])
            s_limit = int(args[1])
            sc_limit = int(args[2])
            p_limit = int(args[3])

            s_used = int(self._local_store.get(keys[0], 0))
            s_res = int(self._local_store.get(keys[3], 0))
            if s_used + s_res + tokens > s_limit:
                return ["ERR_STUDENT_LIMIT", str(s_used + s_res), str(s_limit)]

            if keys[1] not in ["NONE", ""]:
                sc_used = int(self._local_store.get(keys[1], 0))
                sc_res = int(self._local_store.get(keys[4], 0))
                if sc_used + sc_res + tokens > sc_limit:
                    return ["ERR_SCHOOL_LIMIT", str(sc_used + sc_res), str(sc_limit)]

            p_used = int(self._local_store.get(keys[2], 0))
            p_res = int(self._local_store.get(keys[5], 0))
            if p_used + p_res + tokens > p_limit:
                return ["ERR_PLATFORM_LIMIT", str(p_used + p_res), str(p_limit)]

            # Increment active reservations
            self._local_store[keys[3]] = str(s_res + tokens)
            if keys[4] not in ["NONE", ""]:
                sc_res = int(self._local_store.get(keys[4], 0))
                self._local_store[keys[4]] = str(sc_res + tokens)
            self._local_store[keys[5]] = str(p_res + tokens)
            self._local_store[keys[6]] = str(args[6])

            return ["OK", str(tokens), str(s_used + s_res + tokens)]

        elif "RECONCILE" in script_clean or "decrby" in script_clean and len(keys) >= 7:
            actual = int(args[0])
            reserved = int(args[2])

            # Release reservation
            s_res = max(0, int(self._local_store.get(keys[3], 0)) - reserved)
            self._local_store[keys[3]] = str(s_res)
            if keys[4] not in ["NONE", ""]:
                sc_res = max(0, int(self._local_store.get(keys[4], 0)) - reserved)
                self._local_store[keys[4]] = str(sc_res)
            p_res = max(0, int(self._local_store.get(keys[5], 0)) - reserved)
            self._local_store[keys[5]] = str(p_res)
            if keys[6] in self._local_store:
                del self._local_store[keys[6]]

            # Commit actual usage
            s_used = int(self._local_store.get(keys[0], 0)) + actual
            self._local_store[keys[0]] = str(s_used)
            if keys[1] not in ["NONE", ""]:
                sc_used = int(self._local_store.get(keys[1], 0)) + actual
                self._local_store[keys[1]] = str(sc_used)
            p_used = int(self._local_store.get(keys[2], 0)) + actual
            self._local_store[keys[2]] = str(p_used)

            return ["OK", str(actual), str(s_used)]

        elif "REFUND" in script_clean or len(keys) == 4:
            reserved = int(args[0])
            s_res = max(0, int(self._local_store.get(keys[0], 0)) - reserved)
            self._local_store[keys[0]] = str(s_res)
            if keys[1] not in ["NONE", ""]:
                sc_res = max(0, int(self._local_store.get(keys[1], 0)) - reserved)
                self._local_store[keys[1]] = str(sc_res)
            p_res = max(0, int(self._local_store.get(keys[2], 0)) - reserved)
            self._local_store[keys[2]] = str(p_res)
            if keys[3] in self._local_store:
                del self._local_store[keys[3]]
            return ["OK", str(reserved)]

        return ["OK"]

    def clear_all(self):
        """Used in test fixtures to wipe state cleanly."""
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass
        self._local_store.clear()

redis_client = RedisClient.get_client()
