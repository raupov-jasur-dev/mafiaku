import json
import logging
import time
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class InMemoryRedisFallback:
    """In-memory thread-safe store matching Redis async API when Redis server is unreachable."""
    def __init__(self):
        self._store: Dict[str, str] = {}
        self._expires: Dict[str, float] = {}

    def _clean_expired(self):
        now = time.time()
        expired = [k for k, exp in self._expires.items() if exp < now]
        for k in expired:
            self._store.pop(k, None)
            self._expires.pop(k, None)

    async def get(self, key: str) -> Optional[str]:
        self._clean_expired()
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        self._clean_expired()
        if nx and key in self._store:
            return False
        self._store[key] = value
        if ex:
            self._expires[key] = time.time() + ex
        return True

    async def delete(self, key: str) -> int:
        res = 1 if key in self._store else 0
        self._store.pop(key, None)
        self._expires.pop(key, None)
        return res

    async def incr(self, key: str) -> int:
        self._clean_expired()
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._store:
            self._expires[key] = time.time() + seconds
            return True
        return False

    async def keys(self, pattern: str = "*") -> list:
        self._clean_expired()
        # Simple glob-like prefix matching
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self._store if k.startswith(prefix)]
        return list(self._store.keys())

class RedisService:
    def __init__(self):
        self.client = None
        self._fallback = InMemoryRedisFallback()
        self._is_redis_connected = False

    async def connect(self):
        try:
            import redis.asyncio as aioredis
            self.client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.client.ping()
            self._is_redis_connected = True
            logger.info("Successfully connected to Redis instance.")
        except Exception as e:
            if settings.ENVIRONMENT in ("production", "prod"):
                logger.critical(f"FATAL: Redis connection failed in production: {e}")
                raise RuntimeError(f"Redis connection failed in production: {e}")
            logger.warning(f"Could not connect to Redis ({e}). Using In-Memory fallback for development/testing.")
            self._is_redis_connected = False

    async def get(self, key: str) -> Optional[str]:
        if self._is_redis_connected and self.client:
            try:
                return await self.client.get(key)
            except Exception:
                pass
        return await self._fallback.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        if self._is_redis_connected and self.client:
            try:
                return await self.client.set(key, value, ex=ex, nx=nx)
            except Exception:
                pass
        return await self._fallback.set(key, value, ex=ex, nx=nx)

    async def delete(self, key: str) -> int:
        if self._is_redis_connected and self.client:
            try:
                return await self.client.delete(key)
            except Exception:
                pass
        return await self._fallback.delete(key)

    async def incr(self, key: str) -> int:
        if self._is_redis_connected and self.client:
            try:
                return await self.client.incr(key)
            except Exception:
                pass
        return await self._fallback.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        if self._is_redis_connected and self.client:
            try:
                return await self.client.expire(key, seconds)
            except Exception:
                pass
        return await self._fallback.expire(key, seconds)

    async def keys(self, pattern: str = "*") -> list:
        if self._is_redis_connected and self.client:
            try:
                return await self.client.keys(pattern)
            except Exception:
                pass
        return await self._fallback.keys(pattern)

    async def release_lock(self, key: str, token: str) -> bool:
        """Delete a lock only when its owner token still matches."""
        if self._is_redis_connected and self.client:
            try:
                import redis.asyncio as aioredis
                script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
                result = await self.client.eval(script, 1, key, token)
                return bool(result)
            except Exception:
                pass
        current = await self._fallback.get(key)
        if current == token:
            return bool(await self._fallback.delete(key))
        return False

    async def close(self):
        if self._is_redis_connected and self.client:
            await self.client.close()

redis_service = RedisService()
