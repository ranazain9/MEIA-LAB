"""
Filing Cross-Check Agent Implementation
========================================

Retrieves SEC filings, builds a RAG knowledge base,
and verifies earnings call claims against official records.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.agents.base import BaseAgent, AgentInput, AgentOutput
from backend.agents.filing.config import FilingConfig

logger = logging.getLogger(__name__)


class FilingAgent(BaseAgent):
    """
    Agent 3 — Filing Cross-Check.

    Pipeline:
        company ticker → SEC retrieval → chunking → embedding →
        RAG query → numerical verification → consistency score
    """

    AGENT_NAME = "filing_crosscheck"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._filing_config = FilingConfig(**(config or {}))
        self._vector_store = None
        self._embedding_model = None

    @property
    def agent_name(self) -> str:
        return self.AGENT_NAME

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _initialize_impl(self) -> None:
        """Initialize ChromaDB collection and embedding model."""
        logger.info(
            "Filing Agent: initializing vector store at %s",
            self._filing_config.chroma_persist_dir,
        )
        # TODO: Initialize ChromaDB client + collection
        # TODO: Load embedding model

    async def _process_impl(self, agent_input: AgentInput) -> AgentOutput:
        """
        Cross-check earnings call claims against SEC filings.

        Expected input payload keys:
            - ticker (str): Company ticker symbol.
            - claims (list[dict]): Numerical claims from transcript/slides.
            - transcript_segments (list[dict], optional): For context retrieval.

        Returns AgentOutput with data keys:
            - verification_results (list[dict]): Per-claim verification.
            - consistency_score (float): Overall consistency rating.
            - historical_comparison (dict): QoQ / YoY performance deltas.
            - flagged_discrepancies (list[dict]): Claims that don't match filings.
        """
        ticker = agent_input.payload.get("ticker")
        if not ticker:
            return AgentOutput(
                request_id=agent_input.request_id,
                agent_name=self.agent_name,
                success=False,
                errors=["Missing required field: ticker"],
            )

        # TODO: Retrieve SEC filings for the ticker
        # TODO: Chunk and embed filings into ChromaDB
        # TODO: Run RAG retrieval for each claim
        # TODO: Verify numerical consistency
        # TODO: Compute historical comparison

        return AgentOutput(
            request_id=agent_input.request_id,
            agent_name=self.agent_name,
            success=True,
            data={
                "verification_results": [],
                "consistency_score": 0.0,
                "historical_comparison": {},
                "flagged_discrepancies": [],
            },
        )

    async def _shutdown_impl(self) -> None:
        self._vector_store = None
        self._embedding_model = None
        logger.info("Filing Agent: resources released.")
