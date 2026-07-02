"""
LangGraph Workflow Definition
=============================

Defines the state graph for the MEIA orchestration pipeline.
Uses LangGraph for structured, resumable agent workflows.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID

from backend.agents.orchestrator.pipeline import dispatch_pipeline

logger = logging.getLogger(__name__)


class MEIAState(TypedDict, total=False):
    """Shared state that flows through the LangGraph workflow."""

    audio_path: str
    slides_path: str
    ticker: str
    session_id: str

    asr_output: Dict[str, Any]
    vision_output: Dict[str, Any]
    filing_output: Dict[str, Any]

    merged_context: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    report_sections: List[Dict[str, Any]]
    final_report: str

    errors: List[str]
    current_step: str


def build_meia_graph(agent_registry: Any = None, *, parallel: bool = True) -> Any:
    """Build the LangGraph state graph for the MEIA pipeline."""
    try:
        from langgraph.graph import END, START, StateGraph

        def _normalize_session_id(value: Any) -> Optional[UUID]:
            if value in (None, ""):
                return None
            if isinstance(value, UUID):
                return value
            if isinstance(value, str):
                try:
                    return UUID(value)
                except ValueError:
                    return None
            return None

        async def dispatch_agents_node(state: MEIAState) -> MEIAState:
            logger.info("LangGraph: dispatch_agents_node")
            if not agent_registry:
                return {"errors": ["agent_registry not provided"]}

            merged = await dispatch_pipeline(
                agent_registry,
                audio_path=state.get("audio_path", ""),
                slides_path=state.get("slides_path", ""),
                ticker=state.get("ticker", ""),
                session_id=_normalize_session_id(state.get("session_id")),
                parallel=parallel,
            )

            return {
                "asr_output": merged.get("asr_alignment", {}),
                "vision_output": merged.get("vision_analysis", {}),
                "filing_output": merged.get("filing_crosscheck", {}),
                "merged_context": merged,
                "current_step": "finalize",
            }

        graph = StateGraph(MEIAState)
        graph.add_node("dispatch_agents", dispatch_agents_node)
        graph.add_edge(START, "dispatch_agents")
        graph.add_edge("dispatch_agents", END)

        return graph.compile()
    except Exception as exc:
        logger.error("Failed to build LangGraph: %s", exc)
        return None
