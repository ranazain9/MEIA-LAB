import asyncio
import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

class GroqRateLimiter:
    """
    Reusable async rate limiter using asyncio.Semaphore for concurrency limit
    and a sliding window for requests per minute (RPM) limit.
    """

    def __init__(self, max_concurrent: int = 2, requests_per_minute: int = 25) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.requests_per_minute = requests_per_minute
        self.request_timestamps: list[float] = []

    async def __aenter__(self) -> None:
        logger.debug("[Groq] acquiring rate limiter concurrency semaphore")
        await self.semaphore.acquire()

        while True:
            now = time.time()
            # Clean timestamps older than 60 seconds
            self.request_timestamps = [t for t in self.request_timestamps if now - t < 60.0]

            if len(self.request_timestamps) < self.requests_per_minute:
                self.request_timestamps.append(now)
                break
            else:
                oldest_timestamp = self.request_timestamps[0]
                sleep_dur = 60.0 - (now - oldest_timestamp)
                if sleep_dur > 0:
                    logger.info("[Groq] sleeping %.2f sec for rate limiter window to clear", sleep_dur)
                    await asyncio.sleep(sleep_dur)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.semaphore.release()
        logger.debug("[Groq] released rate limiter concurrency semaphore")
