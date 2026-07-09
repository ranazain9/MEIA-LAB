"""
Integration-style unit tests for MEIA agents.

These tests verify agent lifecycle (initialize → process → shutdown),
registry behaviour, and report generation using mocked or in-process
data — no network calls, no GPU, no model downloads required.
"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# AgentRegistry
# ---------------------------------------------------------------------------

class AgentRegistryTests(unittest.TestCase):
    def test_register_and_retrieve(self):
        from backend.agents.registry import AgentRegistry
        from backend.agents.orchestrator.agent import OrchestratorAgent

        registry = AgentRegistry()
        agent = registry.register(OrchestratorAgent)
        self.assertEqual(registry.get("orchestrator"), agent)

    def test_duplicate_registration_raises(self):
        from backend.agents.registry import AgentRegistry
        from backend.agents.orchestrator.agent import OrchestratorAgent

        registry = AgentRegistry()
        registry.register(OrchestratorAgent)
        with self.assertRaises(ValueError):
            registry.register(OrchestratorAgent)

    def test_list_agents(self):
        from backend.agents.registry import AgentRegistry
        from backend.agents.asr.agent import ASRAgent
        from backend.agents.vision.agent import VisionAgent

        registry = AgentRegistry()
        registry.register(ASRAgent)
        registry.register(VisionAgent)
        names = registry.list_agents()
        self.assertIn("asr_alignment", names)
        self.assertIn("vision_analysis", names)

    def test_initialize_all_captures_errors(self):
        """initialize_all should not raise even if an agent fails to init."""
        from backend.agents.registry import AgentRegistry
        from backend.agents.asr.agent import ASRAgent

        registry = AgentRegistry()
        registry.register(ASRAgent)

        # ASRAgent tries to load a HuggingFace model; on test machines
        # this will silently fall back to None (no exception bubbles).
        errors = asyncio.run(registry.initialize_all())
        # errors dict may be empty (success) or contain a message — either is fine
        self.assertIsInstance(errors, dict)

    def test_health_check_all(self):
        from backend.agents.registry import AgentRegistry
        from backend.agents.orchestrator.agent import OrchestratorAgent

        registry = AgentRegistry()
        registry.register(OrchestratorAgent)
        health = asyncio.run(registry.health_check_all())
        self.assertIn("orchestrator", health)
        self.assertIn("initialized", health["orchestrator"])


# ---------------------------------------------------------------------------
# ASRAgent
# ---------------------------------------------------------------------------

class ASRAgentLifecycleTests(unittest.TestCase):
    def test_process_without_initialize_raises(self):
        from backend.agents.asr.agent import ASRAgent
        from backend.agents.base.schemas import AgentInput

        agent = ASRAgent()
        with self.assertRaises(RuntimeError):
            asyncio.run(agent.process(AgentInput(payload={"audio_path": "x.wav"})))

    def test_process_missing_audio_path_returns_failure(self):
        from backend.agents.asr.agent import ASRAgent
        from backend.agents.base.schemas import AgentInput

        agent = ASRAgent()
        # Bypass full init
        agent._initialized = True
        agent._model = None  # no actual model

        result = asyncio.run(agent.process(AgentInput(payload={})))
        self.assertFalse(result.success)
        self.assertTrue(any("audio_path" in e for e in result.errors))

    def test_process_with_fake_model_returns_transcript(self):
        from backend.agents.asr.agent import ASRAgent
        from backend.agents.base.schemas import AgentInput

        class _FakeModel:
            def __call__(self, *a, return_timestamps=True, chunk_length_s=30, generate_kwargs=None):
                return {
                    "chunks": [{"text": "Revenue grew 12 percent.", "timestamp": (0.0, 2.5)}]
                }

        agent = ASRAgent(config={"enable_diarization": False, "enable_tone_analysis": False})
        agent._initialized = True
        agent._model = _FakeModel()

        with patch("backend.agents.asr.processors.librosa") as mock_librosa:
            import numpy as np
            mock_librosa.load.side_effect = Exception("no librosa in test")

            result = asyncio.run(
                agent.process(AgentInput(payload={"audio_path": "fake.wav"}))
            )

        self.assertTrue(result.success)
        self.assertIn("transcript", result.data)
        self.assertGreaterEqual(len(result.data["transcript"]), 1)


# ---------------------------------------------------------------------------
# VisionAgent
# ---------------------------------------------------------------------------

class VisionAgentLifecycleTests(unittest.TestCase):
    def test_process_missing_slides_path_returns_failure(self):
        from backend.agents.vision.agent import VisionAgent
        from backend.agents.base.schemas import AgentInput

        agent = VisionAgent()
        agent._initialized = True
        agent._model = None

        result = asyncio.run(agent.process(AgentInput(payload={})))
        self.assertFalse(result.success)
        self.assertTrue(any("slides_path" in e for e in result.errors))


# ---------------------------------------------------------------------------
# FilingAgent
# ---------------------------------------------------------------------------

class FilingAgentLifecycleTests(unittest.TestCase):
    def test_process_missing_ticker_returns_failure(self):
        from backend.agents.filing.agent import FilingAgent
        from backend.agents.base.schemas import AgentInput

        agent = FilingAgent()
        agent._initialized = True
        agent._vector_store = None
        agent._embedding_model = None

        result = asyncio.run(agent.process(AgentInput(payload={})))
        self.assertFalse(result.success)
        self.assertTrue(any("ticker" in e for e in result.errors))

    @patch("backend.agents.filing.processors.fetch_sec_filings", new_callable=AsyncMock)
    def test_process_no_claims_returns_empty_verification(self, mock_fetch):
        from backend.agents.filing.agent import FilingAgent
        from backend.agents.base.schemas import AgentInput

        mock_fetch.return_value = []  # no filings fetched

        agent = FilingAgent()
        agent._initialized = True
        agent._vector_store = None
        agent._embedding_model = None

        result = asyncio.run(
            agent.process(AgentInput(payload={"ticker": "AMD", "claims": []}))
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["verification_results"], [])
        self.assertEqual(result.data["consistency_score"], 0.0)


# ---------------------------------------------------------------------------
# OrchestratorAgent — report generation
# ---------------------------------------------------------------------------

class OrchestratorReportDuplicateHeadingTests(unittest.TestCase):
    """Ensure the final report does NOT have a duplicate H1 heading."""

    def test_no_duplicate_analyst_brief_heading(self):
        from backend.agents.orchestrator.agent import OrchestratorAgent

        agent = OrchestratorAgent()

        merged = {
            "asr_alignment": {
                "transcript": [{"text": "Revenue grew 12% year over year.", "speaker": "CEO"}],
                "tone_analysis": [{"speaker": "CEO", "confidence": 0.88}],
            },
            "vision_analysis": {
                "kpis": [{"name": "Revenue", "value": "12%"}],
                "guidance": [{"text": "We expect continued growth."}],
            },
            "filing_crosscheck": {
                "verification_results": [{"claim": "Revenue grew 12%", "status": "verified"}],
                "consistency_score": 0.91,
                "flagged_discrepancies": [],
            },
        }

        report = asyncio.run(agent._generate_report(merged, {"ticker": "AMD"}))

        full = report["full_report"]
        # The top-level h1 should appear exactly once
        h1_count = full.count("# AMD Analyst Intelligence Brief")
        self.assertEqual(h1_count, 1, f"Expected exactly 1 H1, found {h1_count}:\n{full[:400]}")

    def test_report_contains_expected_sections(self):
        from backend.agents.orchestrator.agent import OrchestratorAgent

        agent = OrchestratorAgent()
        merged = {
            "asr_alignment": {"transcript": [], "tone_analysis": []},
            "vision_analysis": {"kpis": [], "guidance": []},
            "filing_crosscheck": {
                "verification_results": [],
                "consistency_score": 0.75,
                "flagged_discrepancies": [],
            },
        }
        report = asyncio.run(agent._generate_report(merged, {"ticker": "NVDA"}))
        self.assertIn("NVDA", report["executive_summary"])
        self.assertIn("## Executive Summary", report["full_report"])
        self.assertIn("## Consistency Score", report["full_report"])
        self.assertIn("## Key Risks", report["full_report"])


# ---------------------------------------------------------------------------
# Pipeline — edge cases
# ---------------------------------------------------------------------------

class PipelineEdgeCaseTests(unittest.TestCase):
    def test_extract_claims_empty_inputs(self):
        from backend.agents.orchestrator.pipeline import extract_claims_from_outputs

        claims = extract_claims_from_outputs({}, {})
        self.assertEqual(claims, [])

    def test_extract_claims_deduplicates(self):
        from backend.agents.orchestrator.pipeline import extract_claims_from_outputs

        claims = extract_claims_from_outputs(
            {},
            {
                "kpis": [
                    {"name": "Revenue", "value": "12%"},
                    {"name": "Revenue", "value": "12%"},  # duplicate
                ]
            },
        )
        texts = [c["text"] for c in claims]
        self.assertEqual(len(texts), len(set(texts)), "Claims should be deduplicated")

    def test_kpi_value_empty_string(self):
        from backend.agents.orchestrator.pipeline import kpi_value

        self.assertEqual(kpi_value({}), "")
        self.assertEqual(kpi_value({"value": "  "}), "")


if __name__ == "__main__":
    unittest.main()
