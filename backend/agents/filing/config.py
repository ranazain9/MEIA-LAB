"""
Filing Agent Configuration
==========================
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class FilingConfig(BaseModel):
    """Configuration for the Filing Cross-Check Agent."""

    # SEC EDGAR
    edgar_user_agent: str = Field(
        default="MEIA-LAB meia@example.com",
        description="User-Agent header for SEC EDGAR API requests (Name Email).",
    )
    edgar_base_url: str = "https://efts.sec.gov/LATEST"
    filing_types: list[str] = Field(
        default=["10-K", "10-Q", "8-K"],
        description="SEC filing types to retrieve.",
    )
    max_filings: int = Field(
        default_factory=lambda: int(os.getenv("MEIA_MAX_FILINGS", "2")),
        description="Max historical filings to retrieve per company.",
    )

    # Vector store
    chroma_collection: str = "sec_filings"
    chroma_persist_dir: str = "./data/chromadb"
    embedding_model: str = Field(
        default_factory=lambda: os.getenv("MEIA_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    )
    embedding_provider: str = Field(
        default_factory=lambda: os.getenv("MEIA_EMBEDDING_PROVIDER", "local"),
        description="LangChain embedding provider (aimlapi/hf_cloud/openai/hf/local).",
    )
    embedding_device: str = Field(
        default_factory=lambda: os.getenv("MEIA_EMBEDDING_DEVICE", "cpu"),
        description="Device used for embeddings.",
    )

    # RAG
    retrieval_top_k: int = Field(default=10, ge=1)
    chunk_size: int = Field(default=512, ge=64)
    chunk_overlap: int = Field(default=64, ge=0)

    # Verification
    consistency_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum score to consider a figure consistent.",
    )
