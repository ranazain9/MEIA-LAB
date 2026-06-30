"""
Filing Cross-Check Agent
========================

SEC filing retrieval, historical comparison,
numerical verification, and consistency scoring.

Stack:
    - RAG pipeline with ChromaDB
    - SEC EDGAR integration
"""

from backend.agents.filing.agent import FilingAgent
from backend.agents.filing.config import FilingConfig

__all__ = ["FilingAgent", "FilingConfig"]
