"""Shared MEIA analysis runner used by CLI and API."""

from __future__ import annotations

from typing import Any, Dict

from backend.agents.asr.agent import ASRAgent
from backend.agents.base.schemas import AgentInput, AgentOutput
from backend.agents.filing.agent import FilingAgent
from backend.agents.orchestrator.agent import OrchestratorAgent
from backend.agents.registry import AgentRegistry
from backend.agents.vision.agent import VisionAgent


async def run_analysis(
    audio_path: str,
    slides_path: str,
    ticker: str,
) -> Dict[str, Any]:
    """Run the full MEIA orchestrator pipeline and return JSON-serializable output."""
    registry = AgentRegistry()
    registry.register(ASRAgent)
    registry.register(VisionAgent)
    registry.register(FilingAgent)
    orchestrator = registry.register(OrchestratorAgent)
    orchestrator.set_agent_registry(registry)

    await registry.initialize_all()
    try:
        result: AgentOutput = await orchestrator.process(
            AgentInput(
                payload={
                    "audio_path": audio_path,
                    "slides_path": slides_path,
                    "ticker": ticker.upper(),
                }
            )
        )
        return result.model_dump(mode="json")
    finally:
        await registry.shutdown_all()
