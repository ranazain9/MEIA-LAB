import asyncio
import random
import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

async def execute_with_retry(
    coro_func: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    max_retries: int = 5,
    base_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    """
    Executes an async function with exponential backoff and jitter.
    Retries only on HTTP status codes 429, 500, 502, 503, 504.
    """
    for attempt in range(max_retries + 1):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as exc:
            if attempt == max_retries:
                logger.error("[Groq] maximum retries reached, raising exception")
                raise exc

            # Determine HTTP status code if available
            status_code = getattr(exc, "status_code", None)
            if status_code is None and hasattr(exc, "response"):
                status_code = getattr(exc.response, "status_code", None)

            # Retry only on specified HTTP codes. If not matching, raise immediately.
            if status_code not in {429, 500, 502, 503, 504}:
                logger.debug("[Groq] non-retryable exception: %s (status=%s)", exc, status_code)
                raise exc

            # Calculate backoff with jitter (e.g. base * 2^attempt + random)
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1.0)
            logger.warning("[Groq] retry %d/%d after hitting HTTP %s", attempt + 1, max_retries, status_code)
            logger.info("[Groq] sleeping %.2f sec", delay)
            await asyncio.sleep(delay)
