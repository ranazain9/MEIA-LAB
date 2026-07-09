"""
Orchestrator Pipeline
=====================

Shared dispatch logic for running ASR, Vision, and Filing agents
with claims extracted from upstream outputs.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, Optional
from uuid import UUID

from backend.agents.base import AgentInput, AgentOutput

logger = logging.getLogger(__name__)

_NUMERIC_CLAIM_RE = re.compile(
    r"\b(?:revenue|earnings|eps|margin|growth|profit|sales|income)\b"
    r"[^.\n]{0,50}?\d+(?:\.\d+)?\s*(?:%|percent|million|billion|m|b)\b",
    re.IGNORECASE,
)


def extract_claims_from_outputs(
    asr_data: Dict[str, Any],
    vision_data: Dict[str, Any],
) -> list[dict[str, Any]]:
    """Build filing verification claims from transcript segments and slide KPIs."""
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()

    for kpi in vision_data.get("kpis", []):
        if not isinstance(kpi, dict):
            continue
        name = kpi.get("name") or kpi.get("label") or "KPI"
        value = str(kpi.get("value", "")).strip()
        if not value:
            continue
        text = f"{name}: {value}"
        if text not in seen:
            seen.add(text)
            claims.append({"text": text, "value": value, "source": "slide"})

    for segment in asr_data.get("transcript", []):
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        for match in _NUMERIC_CLAIM_RE.finditer(text):
            fragment = match.group(0).strip()
            if fragment not in seen:
                seen.add(fragment)
                claims.append({"text": fragment, "value": fragment, "source": "transcript"})

    return claims


def kpi_label(kpi: dict[str, Any]) -> str:
    """Return a display label for a KPI dict (supports name or label keys)."""
    return str(kpi.get("name") or kpi.get("label") or "KPI")


def kpi_value(kpi: dict[str, Any]) -> str:
    return str(kpi.get("value", "")).strip()


async def _run_agent(
    agent_registry: Any,
    name: str,
    agent_input: AgentInput,
    timeout: Optional[float] = None,
) -> AgentOutput:
    agent = agent_registry.get(name)
    if hasattr(agent, "is_ready") and not agent.is_ready:
        logger.warning("Agent %s is not ready; skipping execution", name)
        return AgentOutput(
            request_id=agent_input.request_id,
            agent_name=name,
            success=False,
            errors=[f"Agent '{name}' is not ready."],
        )
    if timeout:
        return await asyncio.wait_for(agent.process(agent_input), timeout=timeout)
    return await agent.process(agent_input)


async def dispatch_pipeline(
    agent_registry: Any,
    *,
    audio_path: str = "",
    slides_path: str = "",
    ticker: str = "",
    session_id: Optional[UUID] = None,
    parallel: bool = True,
    agent_timeout_seconds: float = 300.0,
) -> Dict[str, Any]:
    """
    Run ASR and Vision, extract claims, then run Filing verification.

    Returns merged context keyed by agent name.
    """
    phase1: Dict[str, AgentInput] = {}
    if audio_path:
        phase1["asr_alignment"] = AgentInput(
            session_id=session_id,
            payload={"audio_path": audio_path},
        )
    if slides_path:
        phase1["vision_analysis"] = AgentInput(
            session_id=session_id,
            payload={"slides_path": slides_path},
        )

    outputs: Dict[str, AgentOutput] = {}

    if phase1:
        logger.info("Starting phase 1 agents: %s", ", ".join(phase1.keys()))
        if parallel and len(phase1) > 1:
            tasks = [
                _run_agent(agent_registry, name, inp, agent_timeout_seconds)
                for name, inp in phase1.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result_or_exc in zip(phase1.keys(), results):
                if isinstance(result_or_exc, Exception):
                    logger.error(
                        "Pipeline agent failed",
                        extra={"agent": name, "stage": name},
                        exc_info=(type(result_or_exc), result_or_exc, result_or_exc.__traceback__),
                    )
                    outputs[name] = AgentOutput(
                        request_id=phase1[name].request_id,
                        agent_name=name,
                        success=False,
                        data={"error": f"Agent '{name}' failed: {result_or_exc}"},
                        errors=[str(result_or_exc)],
                    )
                else:
                    outputs[name] = result_or_exc
        else:
            for name, inp in phase1.items():
                try:
                    outputs[name] = await _run_agent(
                        agent_registry, name, inp, agent_timeout_seconds
                    )
                except Exception as exc:
                    logger.exception(
                        "Pipeline agent failed",
                        extra={"agent": name, "stage": name},
                    )
                    outputs[name] = AgentOutput(
                        request_id=inp.request_id,
                        agent_name=name,
                        success=False,
                        data={"error": f"Agent '{name}' failed: {exc}"},
                        errors=[str(exc)],
                    )

        succeeded = [n for n, o in outputs.items() if o.success]
        failed = [n for n, o in outputs.items() if not o.success]
        logger.info(
            "Phase 1 complete: succeeded=%s, failed=%s",
            succeeded or "none",
            failed or "none",
        )

    asr_data = outputs["asr_alignment"].data if "asr_alignment" in outputs else {}
    vision_data = outputs["vision_analysis"].data if "vision_analysis" in outputs else {}

    filing_data: Dict[str, Any] = {}
    if ticker:
        claims = extract_claims_from_outputs(asr_data, vision_data)
        logger.info("Extracted %d claims for filing verification", len(claims))
        try:
            logger.info("Starting filing verification for ticker=%s", ticker)
            filing_output = await _run_agent(
                agent_registry,
                "filing_crosscheck",
                AgentInput(
                    session_id=session_id,
                    payload={
                        "ticker": ticker,
                        "claims": claims,
                        "transcript_segments": asr_data.get("transcript", []),
                    },
                ),
                agent_timeout_seconds,
            )
            filing_data = filing_output.data
        except Exception:
            logger.exception(
                "Filing agent failed",
                extra={"agent": "filing_crosscheck", "stage": "FILING"},
            )

    return {
        "asr_alignment": asr_data,
        "vision_analysis": vision_data,
        "filing_crosscheck": filing_data,
    }
