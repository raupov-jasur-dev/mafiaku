import time
from app.services.redis_service import redis_service

class RateLimiter:
    """Token-bucket / Sliding rate limiter for Telegram user commands & callbacks."""
    
    @staticmethod
    async def is_rate_limited(user_id: int, action: str = "general", max_requests: int = 5, window_seconds: int = 2) -> bool:
        key = f"ratelimit:{action}:{user_id}"
        current = await redis_service.incr(key)
        if current == 1:
            await redis_service.expire(key, window_seconds)
        return current > max_requests

rate_limiter = RateLimiter()
