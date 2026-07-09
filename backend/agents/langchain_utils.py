from __future__ import annotations

"""
LangChain-friendly LLM and Embedding helpers for MEIA.
"""
import logging
import os
from typing import Any, Sequence

try:  # pragma: no cover - optional convenience dependency
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional convenience dependency
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

logger = logging.getLogger(__name__)

GROQ_MODEL_ALIASES = {
    "gpt oss 120b": "openai/gpt-oss-120b",
    "gpt-oss-120b": "openai/gpt-oss-120b",
    "gpt oss 20b": "openai/gpt-oss-20b",
    "gpt-oss-20b": "openai/gpt-oss-20b",
    "safety gpt oss 20b": "openai/gpt-oss-safeguard-20b",
    "gpt-oss-safeguard-20b": "openai/gpt-oss-safeguard-20b",
    "llama 4 scout": "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-4-scout": "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama 3.3 70b": "llama-3.3-70b-versatile",
    "qwen 3 32b": "qwen/qwen3-32b",
    "qwen3 32b": "qwen/qwen3-32b",
    "qwen3-32b": "qwen/qwen3-32b",
    "qwen 3.6 27b": "qwen/qwen3.6-27b",
    "qwen3.6 27b": "qwen/qwen3.6-27b",
    "qwen3.6-27b": "qwen/qwen3.6-27b",
}

GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"


def normalize_groq_model_name(model_name: str) -> str:
    """Return the Groq model ID for a friendly name or existing model ID."""
    normalized = model_name.strip()
    return GROQ_MODEL_ALIASES.get(normalized.lower(), normalized)


# ---------------------------------------------------------------------------
# Centralized Groq Chat Model
# ---------------------------------------------------------------------------

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from typing import List, Optional, Any, Iterator, AsyncIterator

class CentralizedGroqChatModel(BaseChatModel):
    model_name: str
    temperature: float = 0.0
    client: Any = None

    class Config:
        arbitrary_types_allowed = True

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))
                )
                return future.result()
        else:
            return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        groq_messages = []
        for msg in messages:
            role = "user"
            if msg.type == "human":
                role = "user"
            elif msg.type == "system":
                role = "system"
            elif msg.type == "ai":
                role = "assistant"
            
            groq_messages.append({"role": role, "content": msg.content})

        response = await self.client.chat(
            messages=groq_messages,
            model=self.model_name,
            temperature=self.temperature,
            **kwargs
        )
        
        text = response.choices[0].message.content
        ai_msg = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        raise NotImplementedError("Streaming is only supported asynchronously via astream")

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        groq_messages = []
        for msg in messages:
            role = "user"
            if msg.type == "human":
                role = "user"
            elif msg.type == "system":
                role = "system"
            elif msg.type == "ai":
                role = "assistant"
            groq_messages.append({"role": role, "content": msg.content})

        response_stream = await self.client.chat(
            messages=groq_messages,
            model=self.model_name,
            temperature=self.temperature,
            stream=True,
            **kwargs
        )
        
        async for chunk in response_stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                chunk_generation = ChatGenerationChunk(
                    message=AIMessageChunk(content=delta)
                )
                yield chunk_generation

    @property
    def _llm_type(self) -> str:
        return "centralized-groq"


# ---------------------------------------------------------------------------
# Local Fallback LLM
# ---------------------------------------------------------------------------

class SimpleLangChainLLM:
    """Fallback LLM when no provider is available."""

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.0,
        provider: str = "local",
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.provider = provider

    def invoke(self, prompt: str) -> str:
        return f"[{self.provider}:{self.model_name}] {prompt}"

    def __call__(self, prompt: str) -> str:
        return self.invoke(prompt)


# ---------------------------------------------------------------------------
# Local Fallback Embeddings
# ---------------------------------------------------------------------------

class SimpleLangChainEmbeddings:
    """Simple deterministic embeddings for development."""

    DIMENSION = 384

    def __init__(self, model_name: str, provider: str = "local") -> None:
        self.model_name = model_name
        self.provider = provider

    def embed_query(self, text: str) -> list[float]:
        seed = float(sum(ord(c) for c in text[:32])) / 1000.0
        return [
            ((seed + i) % 997) / 997.0
            for i in range(self.DIMENSION)
        ]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def embedding_dimension(embedding_model: Any) -> int:
    """Return embedding vector dimension."""
    return len(embedding_model.embed_query("dimension-test"))


# ---------------------------------------------------------------------------
# Build LLM
# ---------------------------------------------------------------------------

def build_llm(
    model_name: str,
    *,
    temperature: float = 0.0,
    provider: str | None = None,
    api_key: str | None = None,
) -> Any:

    provider = (
        provider
        or os.getenv("MEIA_LLM_PROVIDER", "aimlapi")
    ).lower()

    provider_api_keys = {
        "groq": os.getenv("GROQ_API_KEY"),
        "aimlapi": os.getenv("AIMLAPI_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "huggingface": os.getenv("HF_TOKEN"),
    }
    api_key = api_key or provider_api_keys.get(provider)

    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        ChatOpenAI = None

    try:
        from langchain_aimlapi import ChatAIMLAPI
    except Exception:
        ChatAIMLAPI = None

    try:
        from langchain_huggingface import HuggingFaceChatModel
    except Exception:
        HuggingFaceChatModel = None

    logger.info("Using LLM provider: %s", provider)

    if provider == "groq" and api_key:
        from backend.core.groq_client import groq_client
        return CentralizedGroqChatModel(
            model_name=normalize_groq_model_name(model_name),
            temperature=temperature,
            client=groq_client,
        )

    if provider == "aimlapi" and ChatAIMLAPI and api_key:
        return ChatAIMLAPI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )

    if provider == "openai" and ChatOpenAI and api_key:
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )

    if provider == "huggingface" and HuggingFaceChatModel and api_key:
        return HuggingFaceChatModel(
            model=model_name,
            temperature=temperature,
            huggingfacehub_api_token=api_key,
        )

    logger.warning("Using local fallback LLM.")

    return SimpleLangChainLLM(
        model_name=model_name,
        temperature=temperature,
        provider=provider,
    )


# ---------------------------------------------------------------------------
# Build Embeddings
# ---------------------------------------------------------------------------

def build_embeddings(
    model_name: str,
    *,
    provider: str | None = None,
    device: str = "cpu",
    api_key: str | None = None,
) -> Any:

    provider = (
        provider
        or os.getenv("MEIA_EMBEDDING_PROVIDER", "local")
    ).lower()

    if provider == "sentence-transformers":
        provider = "hf"

    api_key = (
        api_key
        or os.getenv("AIMLAPI_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("HF_TOKEN")
    )

    logger.info("Embedding provider: %s", provider)

    if provider == "local":
        embeddings = SimpleLangChainEmbeddings(
            model_name=model_name,
            provider=provider,
        )
        logger.info(
            "Embedding dimension: %d",
            embedding_dimension(embeddings),
        )
        return embeddings

    # -------------------------------------------------------
    # AIMLAPI
    # -------------------------------------------------------

    if provider == "aimlapi":
        try:
            from langchain_aimlapi import AimlapiEmbeddings

            embeddings = AimlapiEmbeddings(
                model=model_name,
                api_key=api_key,
            )

            logger.info(
                "Embedding dimension: %d",
                embedding_dimension(embeddings),
            )

            return embeddings

        except Exception as e:
            logger.warning("AIMLAPI failed: %s", e)

    # -------------------------------------------------------
    # OpenAI
    # -------------------------------------------------------

    if provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings(
                model=model_name,
                api_key=api_key,
            )

            logger.info(
                "Embedding dimension: %d",
                embedding_dimension(embeddings),
            )

            return embeddings

        except Exception as e:
            logger.warning("OpenAI failed: %s", e)

    # -------------------------------------------------------
    # HuggingFace Local
    # -------------------------------------------------------

    if provider == "hf":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={
                    "device": device,
                },
                encode_kwargs={
                    "normalize_embeddings": False,
                },
            )

            logger.info(
                "Embedding dimension: %d",
                embedding_dimension(embeddings),
            )

            return embeddings

        except Exception as e:
            logger.warning("HF Local failed: %s", e)

    # -------------------------------------------------------
    # HuggingFace Endpoint
    # -------------------------------------------------------

    if provider == "hf_endpoint":
        try:
            from langchain_huggingface import HuggingFaceEndpointEmbeddings

            embeddings = HuggingFaceEndpointEmbeddings(
                model=model_name,
                huggingfacehub_api_token=api_key,
            )

            logger.info(
                "Embedding dimension: %d",
                embedding_dimension(embeddings),
            )

            return embeddings

        except Exception as e:
            logger.warning("HF Endpoint failed: %s", e)

    # -------------------------------------------------------
    # Fallback
    # -------------------------------------------------------

    logger.warning("Using local fallback embeddings.")

    embeddings = SimpleLangChainEmbeddings(
        model_name=model_name,
        provider=provider,
    )

    logger.info(
        "Embedding dimension: %d",
        embedding_dimension(embeddings),
    )

    return embeddings
