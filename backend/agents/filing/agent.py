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
from backend.agents.langchain_utils import build_embeddings

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
        self._embedding_model = build_embeddings(
            self._filing_config.embedding_model,
            provider=self._filing_config.embedding_provider,
            device=self._filing_config.embedding_device,
        )
        try:
            from langchain_chroma import Chroma
            self._vector_store = Chroma(
                collection_name=self._filing_config.chroma_collection,
                embedding_function=self._embedding_model,
                persist_directory=self._filing_config.chroma_persist_dir,
            )
            logger.info("ChromaDB initialized successfully.")
        except Exception as exc:
            logger.error("Failed to initialize ChromaDB: %s", exc)
            self._vector_store = None
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

        claims = agent_input.payload.get("claims", [])
        
        try:
            from backend.agents.filing.processors import (
                fetch_sec_filings,
                chunk_filing_text,
                embed_and_store,
                verify_claim,
                compute_historical_comparison,
            )
            
            # Step 1: Retrieve SEC filings
            filings = await fetch_sec_filings(
                ticker,
                self._filing_config.filing_types,
                self._filing_config.max_filings,
                self._filing_config.edgar_user_agent
            )
            
            # Step 2: Chunk and embed
            if self._vector_store:
                for filing in filings:
                    chunks = await chunk_filing_text(
                        filing.content,
                        self._filing_config.chunk_size,
                        self._filing_config.chunk_overlap
                    )
                    await embed_and_store(
                        chunks,
                        {"source": filing.url, "type": filing.filing_type, "ticker": ticker},
                        self._vector_store,
                        self._embedding_model
                    )

            # Step 3: Verify claims
            verification_results = []
            flagged = []
            consistency_sum = 0.0
            
            for claim in claims:
                res = await verify_claim(
                    claim,
                    self._vector_store,
                    self._embedding_model,
                    self._filing_config.retrieval_top_k
                )
                res_dict = res.__dict__ if hasattr(res, "__dict__") else {}
                res_dict["status"] = "verified" if res.is_consistent else "flagged"
                verification_results.append(res_dict)
                consistency_sum += res.confidence
                if not res.is_consistent and res.confidence > 0.5:
                    flagged.append(res_dict)
                    
            consistency_score = consistency_sum / len(claims) if claims else 0.0

            # Step 4: Historical comparisons
            # We mock metric extraction for now
            historical_comparison = await compute_historical_comparison(filings, ["Revenue", "EPS"])
            historical_dict = [h.__dict__ if hasattr(h, "__dict__") else {} for h in historical_comparison]
            
        except Exception as exc:
            logger.error("Error in FilingAgent pipeline: %s", exc)
            return AgentOutput(
                request_id=agent_input.request_id,
                agent_name=self.agent_name,
                success=False,
                errors=[str(exc)],
            )

        return AgentOutput(
            request_id=agent_input.request_id,
            agent_name=self.agent_name,
            success=True,
            data={
                "verification_results": verification_results,
                "consistency_score": consistency_score,
                "historical_comparison": historical_dict,
                "flagged_discrepancies": flagged,
            },
        )

    async def _shutdown_impl(self) -> None:
        self._vector_store = None
        self._embedding_model = None
        logger.info("Filing Agent: resources released.")
