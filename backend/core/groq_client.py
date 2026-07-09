import os
import logging
from typing import Any, List, Dict, Optional
from groq import AsyncGroq
from backend.core.rate_limiter import GroqRateLimiter
from backend.core.retry import execute_with_retry

logger = logging.getLogger(__name__)

class GroqClient:
    """
    Centralized Groq API client wrapping requests with rate limiting,
    reusable retry logic, and automatic retry support.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_concurrent: int = 2,
        requests_per_minute: int = 25,
        max_retries: int = 5,
    ) -> None:
        self._api_key = api_key
        self.max_retries = max_retries
        self._client_instance: Optional[AsyncGroq] = None
        self.limiter = GroqRateLimiter(
            max_concurrent=max_concurrent,
            requests_per_minute=requests_per_minute
        )

    @property
    def client(self) -> AsyncGroq:
        if self._client_instance is None:
            import httpx
            api_key = self._api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.warning("GROQ_API_KEY is not set. API calls will fail.")
                api_key = "dummy_key_for_import_time"
            self._client_instance = AsyncGroq(
                api_key=api_key,
                timeout=httpx.Timeout(300.0),  # 5-minute timeout for long transcriptions and vision batches
            )
        return self._client_instance


    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.0,
        stream: bool = False,
        **kwargs: Any
    ) -> Any:
        async def _call():
            logger.info("[Groq] request started")
            res = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                stream=stream,
                **kwargs
            )
            logger.info("[Groq] request completed")
            return res

        async def _limited_call():
            logger.info("[Groq] waiting for rate limiter")
            async with self.limiter:
                return await execute_with_retry(_call, max_retries=self.max_retries)

        return await _limited_call()

    async def vision(
        self,
        messages: List[Dict[str, Any]],
        model: str = "llama-3.2-11b-vision-preview",
        temperature: float = 0.0,
        **kwargs: Any
    ) -> Any:
        return await self.chat(messages=messages, model=model, temperature=temperature, **kwargs)

    async def transcription(
        self,
        file: Any,
        model: str = "whisper-large-v3",
        response_format: str = "verbose_json",
        language: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> Any:
        async def _call():
            logger.info("[Groq] request started")
            res = await self.client.audio.transcriptions.create(
                file=file,
                model=model,
                response_format=response_format,
                language=language or "en",
                temperature=temperature,
                **kwargs
            )
            logger.info("[Groq] request completed")
            return res

        async def _limited_call():
            logger.info("[Groq] waiting for rate limiter")
            async with self.limiter:
                return await execute_with_retry(_call, max_retries=self.max_retries)

        return await _limited_call()


# Initialize global client
groq_client = GroqClient(
    api_key=os.getenv("GROQ_API_KEY"),
    max_concurrent=int(os.getenv("MEIA_GROQ_MAX_CONCURRENT", "2")),
    requests_per_minute=int(os.getenv("MEIA_GROQ_REQUESTS_PER_MINUTE", "25")),
    max_retries=int(os.getenv("MEIA_GROQ_MAX_RETRIES", "5")),
)
