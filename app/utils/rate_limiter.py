# ============================================================
# app/utils/rate_limiter.py — Avoid API rate limit issues
# ============================================================
import asyncio
import time
from collections import deque

from app.config import settings


class RateLimiter:
    def __init__(self, requests_per_minute: int = None):
        self.limit = requests_per_minute or settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.window_seconds = 60
        self._timestamps = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()

            while self._timestamps and now - self._timestamps[0] > self.window_seconds:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.limit:
                wait_time = self.window_seconds - (now - self._timestamps[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self._timestamps.append(time.monotonic())

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


llm_rate_limiter = RateLimiter()
git_api_rate_limiter = RateLimiter(requests_per_minute=60)