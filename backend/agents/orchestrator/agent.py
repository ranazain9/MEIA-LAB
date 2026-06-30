"""
Orchestrator Agent Implementation
==================================

Coordinates the ASR, Vision, and Filing agents, then synthesizes
their outputs into a unified Analyst Intelligence Brief.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from backend.agents.base import BaseAgent, AgentInput, AgentOutput
from backend.agents.orchestrator.config import OrchestratorConfig

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
        self._graph = None  # LangGraph state graph
        self._agent_registry = None

    @property
    def agent_name(self) -> str:
        return self.AGENT_NAME

    def set_agent_registry(self, registry: Any) -> None:
        """Inject the agent registry for dispatching to sub-agents."""
        self._agent_registry = registry

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _initialize_impl(self) -> None:
        """Load the LLM and build the LangGraph workflow."""
        logger.info(
            "Orchestrator: loading LLM=%s", self._orch_config.llm_model
        )
        # TODO: Load Llama 3.1 model
        # TODO: Build LangGraph state graph

    async def _process_impl(self, agent_input: AgentInput) -> AgentOutput:
        """
        Run the full orchestration pipeline.

        Expected input payload keys:
            - audio_path (str): Earnings call audio.
            - slides_path (str): Earnings presentation.
            - ticker (str): Company ticker symbol.

        Returns AgentOutput with data keys:
            - executive_summary (str)
            - tone_analysis (dict)
            - consistency_score (float)
            - risk_factors (list[dict])
            - slide_speech_comparison (list[dict])
            - historical_comparison (dict)
            - full_report (str): Complete Analyst Intelligence Brief.
        """
        payload = agent_input.payload

        # Step 1: Dispatch to sub-agents
        sub_outputs = await self._dispatch_agents(agent_input)

        # Step 2: Merge outputs
        merged = self._merge_outputs(sub_outputs)

        # Step 3: Synthesize with LLM
        # TODO: Run LLM synthesis via LangGraph
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

    # ------------------------------------------------------------------
    # Internal orchestration
    # ------------------------------------------------------------------

    async def _dispatch_agents(
        self, agent_input: AgentInput
    ) -> Dict[str, AgentOutput]:
        """Dispatch work to ASR, Vision, and Filing agents."""
        if self._agent_registry is None:
            raise RuntimeError("Agent registry not set on orchestrator.")

        tasks: Dict[str, Any] = {}
        payload = agent_input.payload

        # Build per-agent inputs
        if payload.get("audio_path"):
            asr_input = AgentInput(
                session_id=agent_input.session_id,
                payload={"audio_path": payload["audio_path"]},
            )
            tasks["asr_alignment"] = asr_input

        if payload.get("slides_path"):
            vision_input = AgentInput(
                session_id=agent_input.session_id,
                payload={"slides_path": payload["slides_path"]},
            )
            tasks["vision_analysis"] = vision_input

        if payload.get("ticker"):
            filing_input = AgentInput(
                session_id=agent_input.session_id,
                payload={"ticker": payload["ticker"]},
            )
            tasks["filing_crosscheck"] = filing_input

        # Execute
        if self._orch_config.parallel_agents:
            results = await self._run_parallel(tasks)
        else:
            results = await self._run_sequential(tasks)

        return results

    async def _run_parallel(
        self, tasks: Dict[str, AgentInput]
    ) -> Dict[str, AgentOutput]:
        """Run agents concurrently with timeout."""
        async def _run_one(name: str, inp: AgentInput) -> tuple[str, AgentOutput]:
            agent = self._agent_registry.get(name)
            output = await asyncio.wait_for(
                agent.process(inp),
                timeout=self._orch_config.agent_timeout_seconds,
            )
            return name, output

        coros = [_run_one(n, i) for n, i in tasks.items()]
        results = await asyncio.gather(*coros, return_exceptions=True)

        outputs: Dict[str, AgentOutput] = {}
        for r in results:
            if isinstance(r, Exception):
                logger.error("Agent failed: %s", r)
            else:
                outputs[r[0]] = r[1]
        return outputs

    async def _run_sequential(
        self, tasks: Dict[str, AgentInput]
    ) -> Dict[str, AgentOutput]:
        """Run agents one at a time."""
        outputs: Dict[str, AgentOutput] = {}
        for name, inp in tasks.items():
            agent = self._agent_registry.get(name)
            outputs[name] = await agent.process(inp)
        return outputs

    def _merge_outputs(
        self, outputs: Dict[str, AgentOutput]
    ) -> Dict[str, Any]:
        """Combine all agent outputs into a single context dict."""
        merged: Dict[str, Any] = {}
        for name, output in outputs.items():
            merged[name] = output.data
        return merged

    async def _generate_report(
        self,
        merged: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use the LLM to synthesize the final intelligence report."""
        # TODO: Build prompts and run LLM inference
        # TODO: Structure output into report sections
        return {
            "executive_summary": "",
            "tone_analysis": {},
            "consistency_score": 0.0,
            "risk_factors": [],
            "slide_speech_comparison": [],
            "historical_comparison": {},
            "full_report": "",
        }

    async def _shutdown_impl(self) -> None:
        self._llm = None
        self._graph = None
        logger.info("Orchestrator: resources released.")
