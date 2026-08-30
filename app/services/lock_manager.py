import time
import asyncio
import uuid
from typing import Optional
from app.services.redis_service import redis_service

class DistributedLock:
    def __init__(self, key: str, timeout: int = 10):
        self.lock_key = f"lock:{key}"
        self.timeout = timeout
        self.acquired = False
        self.token = uuid.uuid4().hex

    async def __aenter__(self):
        start = time.time()
        while time.time() - start < 3.0: # Try for up to 3 seconds
            res = await redis_service.set(self.lock_key, self.token, ex=self.timeout, nx=True)
            if res:
                self.acquired = True
                return self
            await asyncio.sleep(0.05)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            await redis_service.release_lock(self.lock_key, self.token)

def acquire_lock(name: str, timeout: int = 10) -> DistributedLock:
    return DistributedLock(name, timeout=timeout)
