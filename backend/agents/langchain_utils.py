from __future__ import annotations

"""LangChain-friendly model and embedding helpers for MEIA agents."""

import os
from typing import Any, Sequence


class SimpleLangChainLLM:
    """Small adapter used when LangChain packages are unavailable."""

    def __init__(self, model_name: str, temperature: float = 0.0, provider: str = "local") -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.provider = provider

    def invoke(self, prompt: str) -> str:
        return f"[{self.provider}:{self.model_name}] {prompt}"

    def __call__(self, prompt: str) -> str:
        return self.invoke(prompt)


class SimpleLangChainEmbeddings:
    """Simple deterministic embedding adapter for local scaffolding."""

    def __init__(self, model_name: str, provider: str = "local") -> None:
        self.model_name = model_name
        self.provider = provider

    def embed_query(self, text: str) -> list[float]:
        return [float(sum(ord(ch) for ch in text[:8])) / 1000.0] * 8

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]


def build_llm(
    model_name: str,
    *,
    temperature: float = 0.0,
    provider: str | None = None,
    api_key: str | None = None,
) -> Any:
    """Create a LangChain-like LLM object.

    Uses real LangChain integrations when available and falls back to a local adapter
    for lightweight local development and tests.
    """

    provider = provider or os.getenv("MEIA_LLM_PROVIDER", "aimlapi")
    api_key = (
        api_key
        or os.getenv("AIMLAPI_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("HF_TOKEN")
    )

    try:
        from langchain_openai import ChatOpenAI  # type: ignore
    except Exception:
        ChatOpenAI = None

    try:
        from langchain_aimlapi import ChatAIMLAPI  # type: ignore
    except Exception:
        ChatAIMLAPI = None

    if provider == "aimlapi" and ChatAIMLAPI is not None and api_key:
        return ChatAIMLAPI(model=model_name, temperature=temperature, api_key=api_key)

    if provider == "openai" and ChatOpenAI is not None and api_key:
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)

    return SimpleLangChainLLM(model_name=model_name, temperature=temperature, provider=provider)


def build_embeddings(
    model_name: str,
    *,
    provider: str | None = None,
    device: str = "cpu",
) -> Any:
    """Create a LangChain-like embedding object."""

    provider = provider or os.getenv("MEIA_EMBEDDING_PROVIDER", "hf")

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
    except Exception:
        HuggingFaceEmbeddings = None

    if provider == "hf" and HuggingFaceEmbeddings is not None:
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": False},
        )

    return SimpleLangChainEmbeddings(model_name=model_name, provider=provider)
