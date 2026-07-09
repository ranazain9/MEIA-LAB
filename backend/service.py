"""Shared MEIA analysis runner used by CLI and API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import logging

try:  # pragma: no cover - optional convenience dependency
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional convenience dependency
    load_dotenv = None

from backend.agents.asr.agent import ASRAgent
from backend.agents.base.schemas import AgentInput, AgentOutput
from backend.agents.filing.agent import FilingAgent
from backend.agents.orchestrator.agent import OrchestratorAgent
from backend.agents.orchestrator.pipeline import dispatch_pipeline
from backend.agents.registry import AgentRegistry
from backend.agents.vision.agent import VisionAgent

ROOT_DIR = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger(__name__)


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

    logger.info("Initializing MEIA agents for ticker=%s", ticker.upper())
    await registry.initialize_all()
    try:
        request = AgentInput(
            payload={
                "audio_path": audio_path,
                "slides_path": slides_path,
                "ticker": ticker.upper(),
            }
        )
        try:
            logger.info("Running orchestrator for ticker=%s", ticker.upper())
            result: AgentOutput = await orchestrator.process(request)
            logger.info(
                "Orchestrator returned: success=%s, data_keys=%s",
                result.success,
                list(result.data.keys()),
            )

            # Reshape: promote data keys to top level so callers get
            # executive_summary, transcript, slide_analysis, etc. directly.
            envelope = result.model_dump(mode="json")
            data = envelope.get("data") or {}
            shaped: Dict[str, Any] = {
                # Required keys expected by the frontend / requirement spec
                "executive_summary": data.get("executive_summary", ""),
                "transcript": data.get("transcript", []),
                "slide_analysis": data.get("slide_analysis", {}),
                "filing_verification": data.get("filing_verification", {}),
                "risks": data.get("risks", data.get("risk_factors", [])),
                "confidence": data.get("confidence", data.get("consistency_score", 0.0)),
                "metadata": {
                    **envelope.get("metadata", {}),
                    "agent_name": envelope.get("agent_name", ""),
                    "success": envelope.get("success", True),
                    "errors": envelope.get("errors", []),
                },
                # Preserve additional detail fields
                "tone_analysis": data.get("tone_analysis", {}),
                "consistency_score": data.get("consistency_score", 0.0),
                "risk_factors": data.get("risk_factors", []),
                "slide_speech_comparison": data.get("slide_speech_comparison", []),
                "historical_comparison": data.get("historical_comparison", {}),
                "full_report": data.get("full_report", ""),
            }
            logger.info(
                "Result stored for ticker=%s, top-level keys=%s",
                ticker.upper(),
                list(shaped.keys()),
            )
            return shaped
        except Exception as exc:
            logger.exception("Orchestrator failed; running partial fallback")
            merged = await dispatch_pipeline(
                registry,
                audio_path=audio_path,
                slides_path=slides_path,
                ticker=ticker.upper(),
                session_id=request.session_id,
                parallel=True,
            )
            filing_fb = merged.get("filing_crosscheck") or {}
            asr_fb = merged.get("asr_alignment") or {}
            vision_fb = merged.get("vision_analysis") or {}
            fallback_summary = (
                f"{ticker.upper()} analysis completed with partial data "
                "because the orchestrator failed."
            )
            return AgentOutput(
                request_id=request.request_id,
                agent_name=orchestrator.agent_name,
                success=False,
                data={
                    "executive_summary": fallback_summary,
                    # Required top-level keys
                    "transcript": asr_fb.get("transcript", []),
                    "slide_analysis": vision_fb,
                    "filing_verification": filing_fb,
                    "risks": filing_fb.get("flagged_discrepancies", []),
                    "confidence": filing_fb.get("consistency_score", 0.0),
                    # Legacy / additional
                    "tone_analysis": asr_fb,
                    "consistency_score": filing_fb.get("consistency_score", 0.0),
                    "risk_factors": filing_fb.get("flagged_discrepancies", []),
                    "slide_speech_comparison": vision_fb.get("kpis", []),
                    "historical_comparison": filing_fb.get("historical_comparison", {}),
                    "full_report": (
                        f"# {ticker.upper()} Analyst Intelligence Brief\n\n"
                        "## Partial Analysis\n"
                        "The orchestrator failed, but the sub-agent outputs were preserved."
                    ),
                    "verification_results": filing_fb.get("verification_results", []),
                },
                errors=[str(exc)],
                metadata={"partial_fallback": True},
            ).model_dump(mode="json")
    finally:
        await registry.shutdown_all()
