"""
Orchestrator Agent Implementation
==================================

Coordinates the ASR, Vision, and Filing agents, then synthesizes
their outputs into a unified Analyst Intelligence Brief.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.agents.base import BaseAgent, AgentInput, AgentOutput
from backend.agents.base.schemas import IntelligenceReport
from backend.agents.langchain_utils import build_llm
from backend.agents.orchestrator.config import OrchestratorConfig
from backend.agents.orchestrator.pipeline import dispatch_pipeline, kpi_label, kpi_value
from backend.agents.orchestrator.processors import (
    EXECUTIVE_SUMMARY_PROMPT,
    ReportSection,
    detect_risks,
    format_report_markdown,
)
from backend.agents.orchestrator.utils import format_prompt, truncate_to_token_limit

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Agent 4 — Orchestrator & Report Generator.

    Workflow (LangGraph):
        1. Dispatch inputs to ASR, Vision, Filing agents (parallel or sequential)
        2. Collect and merge outputs
        3. Run LLM synthesis for insight extraction
        4. Detect risks and anomalies
        5. Generate Analyst Intelligence Brief
    """

    AGENT_NAME = "orchestrator"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._orch_config = OrchestratorConfig(**(config or {}))
        self._llm = None
        self._graph = None
        self._agent_registry = None

    @property
    def agent_name(self) -> str:
        return self.AGENT_NAME

    def set_agent_registry(self, registry: Any) -> None:
        """Inject the agent registry for dispatching to sub-agents."""
        self._agent_registry = registry

    async def _initialize_impl(self) -> None:
        """Load the LLM and build the LangGraph workflow."""
        logger.info(
            "Orchestrator: loading LLM=%s provider=%s",
            self._orch_config.llm_model,
            self._orch_config.llm_provider,
        )
        self._llm = build_llm(
            self._orch_config.llm_model,
            temperature=self._orch_config.temperature,
            provider=self._orch_config.llm_provider,
        )
        from backend.agents.orchestrator.graph import build_meia_graph

        self._graph = build_meia_graph(
            self._agent_registry,
            parallel=self._orch_config.parallel_agents,
        )
        if self._graph is None:
            logger.warning("Orchestrator: failed to build LangGraph workflow.")

    async def _process_impl(self, agent_input: AgentInput) -> AgentOutput:
        """Run the full orchestration pipeline."""
        payload = agent_input.payload

        if self._graph is not None:
            initial_state = {
                "audio_path": payload.get("audio_path", ""),
                "slides_path": payload.get("slides_path", ""),
                "ticker": payload.get("ticker", ""),
                "session_id": str(agent_input.session_id) if agent_input.session_id else "",
            }
            final_state = await self._graph.ainvoke(initial_state)
            merged = final_state.get("merged_context", {})
        else:
            merged = await dispatch_pipeline(
                self._agent_registry,
                audio_path=payload.get("audio_path", ""),
                slides_path=payload.get("slides_path", ""),
                ticker=payload.get("ticker", ""),
                session_id=agent_input.session_id,
                parallel=self._orch_config.parallel_agents,
                agent_timeout_seconds=self._orch_config.agent_timeout_seconds,
            )

        report = await self._generate_report(merged, payload)

        return AgentOutput(
            request_id=agent_input.request_id,
            agent_name=self.agent_name,
            success=True,
            data={
                "executive_summary": report.get("executive_summary", ""),
                "tone_analysis": report.get("tone_analysis", {}),
                "consistency_score": report.get("consistency_score", 0.0),
                "risk_factors": report.get("risk_factors", []),
                "slide_speech_comparison": report.get("slide_speech_comparison", []),
                "historical_comparison": report.get("historical_comparison", {}),
                "full_report": report.get("full_report", ""),
            },
        )

    async def _generate_report(
        self,
        merged: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesize a structured intelligence report from sub-agent outputs."""
        ticker = payload.get("ticker") or "the company"
        asr_data = merged.get("asr_alignment", {}) or {}
        vision_data = merged.get("vision_analysis", {}) or {}
        filing_data = merged.get("filing_crosscheck", {}) or {}

        transcript = asr_data.get("transcript", [])
        tone_analysis = asr_data.get("tone_analysis", [])
        kpis = vision_data.get("kpis", [])
        guidance = vision_data.get("guidance", [])
        verification = filing_data.get("verification_results", [])
        flagged = filing_data.get("flagged_discrepancies", [])
        consistency_score = filing_data.get("consistency_score", 0.0)
        historical = filing_data.get("historical_comparison", {})

        transcript_text = " ".join(
            segment.get("text", "") for segment in transcript if isinstance(segment, dict)
        ).strip()
        kpi_text = ", ".join(
            f"{kpi_label(item)}={kpi_value(item)}"
            for item in kpis
            if isinstance(item, dict) and kpi_value(item)
        )
        guidance_text = ". ".join(
            item if isinstance(item, str) else item.get("text", "")
            for item in guidance
            if (isinstance(item, str) and item) or (isinstance(item, dict) and item.get("text"))
        )

        filing_summary = (
            f"Consistency score: {consistency_score:.2f}; "
            f"verified {len(verification)} claims; "
            f"flagged {len(flagged)} discrepancies."
        )

        executive_summary = ""
        if self._llm is not None:
            try:
                prompt = format_prompt(
                    EXECUTIVE_SUMMARY_PROMPT,
                    transcript_summary=truncate_to_token_limit(transcript_text[:800]),
                    slide_summary=truncate_to_token_limit(
                        f"KPIs: {kpi_text}. Guidance: {guidance_text}"[:800]
                    ),
                    filing_summary=filing_summary,
                )
                response = self._llm.invoke(prompt)
                executive_summary = getattr(response, "content", str(response)).strip()
            except Exception as exc:
                logger.warning("LLM executive summary failed: %s", exc)

        if not executive_summary:
            summary_parts = [f"{ticker} earnings call analysis"]
            if transcript_text:
                summary_parts.append(transcript_text[:220])
            if kpi_text:
                summary_parts.append(f"Key slide metrics: {kpi_text}.")
            if guidance_text:
                summary_parts.append(guidance_text[:220])
            executive_summary = " ".join(part for part in summary_parts if part).strip()
        if not executive_summary:
            executive_summary = (
                f"{ticker} earnings call review completed with structured multimodal analysis."
            )

        risk_factors = self._build_risk_factors(verification, flagged, filing_data)
        if self._orch_config.include_risk_detection and self._llm is not None:
            llm_risks = await detect_risks(merged, self._llm)
            for factor in llm_risks:
                risk_factors.append(
                    {
                        "label": factor.category,
                        "description": factor.description,
                        "severity": factor.severity,
                    }
                )

        slide_speech_comparison: List[Dict[str, Any]] = []
        for item in kpis:
            if not isinstance(item, dict):
                continue
            slide_speech_comparison.append(
                {
                    "slide_metric": f"{kpi_label(item)}={kpi_value(item)}",
                    "speech_reference": transcript_text[:160] or "No transcript excerpt available",
                    "status": "reviewed",
                }
            )

        sections = [
            ReportSection(title="Executive Summary", content=executive_summary, order=1),
            ReportSection(
                title="Consistency Score",
                content=f"{consistency_score:.2f}",
                order=2,
            ),
            ReportSection(
                title="Key Risks",
                content="\n".join(
                    f"- {r['label']}: {r['description']}" for r in risk_factors
                )
                or "No material risks identified.",
                order=3,
            ),
        ]
        if kpi_text:
            sections.append(
                ReportSection(title="Key Financial Metrics", content=kpi_text, order=4)
            )

        full_report = await format_report_markdown(sections)
        full_report = f"# {ticker} Analyst Intelligence Brief\n\n{full_report}"

        report = IntelligenceReport(
            executive_summary=executive_summary,
            tone_analysis={
                "speaker_count": len(
                    [
                        item
                        for item in tone_analysis
                        if isinstance(item, dict) and item.get("speaker")
                    ]
                ),
                "segments": tone_analysis,
            },
            consistency_score=float(consistency_score),
            risk_factors=risk_factors,
            slide_speech_comparison=slide_speech_comparison,
            historical_comparison=historical or {},
            full_report=full_report,
        )

        return report.model_dump()

    def _build_risk_factors(
        self,
        verification: List[Any],
        flagged: List[Any],
        filing_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Derive rule-based risk factors from filing verification output."""
        if flagged:
            return [
                {
                    "label": "Filing mismatch",
                    "description": (
                        f"{len(flagged)} claim(s) inconsistent with SEC filing evidence."
                    ),
                    "severity": "high",
                }
            ]

        if verification:
            inconsistent = [
                item
                for item in verification
                if isinstance(item, dict)
                and (
                    item.get("is_consistent") is False
                    or item.get("status") == "flagged"
                )
            ]
            if inconsistent:
                return [
                    {
                        "label": "Filing mismatch",
                        "description": "One or more claims were flagged during filing verification.",
                        "severity": "high",
                    }
                ]
            return [
                {
                    "label": "Consistency check",
                    "description": "Reviewed statements were consistent with available filing evidence.",
                    "severity": "low",
                }
            ]

        if filing_data:
            return [
                {
                    "label": "Limited verification",
                    "description": "Filing agent ran but no claims were available to verify.",
                    "severity": "medium",
                }
            ]

        return [
            {
                "label": "Insufficient evidence",
                "description": "No filing verification results were available for this run.",
                "severity": "medium",
            }
        ]

    async def _shutdown_impl(self) -> None:
        self._llm = None
        self._graph = None
        logger.info("Orchestrator: resources released.")
