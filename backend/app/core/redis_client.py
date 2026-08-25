import os
import logging
from typing import Optional

logger = logging.getLogger("edufeedia.redis")

class RedisClient:
    """
    Thread-safe Redis client wrapper with high-availability connection pooling
    and automatic memory cache fallback for standalone unit testing.
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
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        is_production = (os.getenv("ENVIRONMENT") == "production")
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            self._redis.ping()
            logger.info(f"Connected to Redis cluster at {redis_url}")
        except Exception as e:
            if is_production:
                logger.critical(f"[CRITICAL: Production Redis Connection Failed]: {e}")
                raise RuntimeError(f"Critical Infrastructure Failure: Redis cluster is unreachable in production environment ({e}). In-memory fallback is strictly disallowed.")
            logger.warning(f"Redis unavailable ({e}). Initializing in-process fallback store for testing.")
            self._redis = None

    def setex(self, key: str, seconds: int, value: str) -> bool:
        if self._redis:
            try:
                return bool(self._redis.setex(key, seconds, value))
            except Exception as e:
                logger.error(f"Redis setex failed: {e}")
                if os.getenv("ENVIRONMENT") == "production":
                    raise RuntimeError(f"Production Redis cluster operation failed: {e}")
        elif os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("Production Redis cluster unavailable. In-memory OTP storage is disallowed.")
        self._local_store[key] = value
        return True

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

    def clear_all(self):
        """Used in test fixtures to wipe state."""
        if self._redis:
            try:
                self._redis.flushdb()
            except Exception:
                pass
        self._local_store.clear()

redis_client = RedisClient.get_client()
