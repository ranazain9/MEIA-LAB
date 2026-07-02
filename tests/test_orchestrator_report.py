import asyncio
import unittest

from backend.agents.orchestrator.agent import OrchestratorAgent


class OrchestratorReportTests(unittest.TestCase):
    def test_generate_report_uses_agent_payloads(self):
        agent = OrchestratorAgent(config={"report_format": "json"})

        merged = {
            "asr_alignment": {
                "transcript": [
                    {"text": "Revenue grew 12% year over year.", "speaker": "CEO"}
                ],
                "tone_analysis": [{"speaker": "CEO", "confidence": 0.88}],
            },
            "vision_analysis": {
                "kpis": [{"name": "Revenue", "value": "12%"}],
                "guidance": [{"text": "We expect continued growth."}],
            },
            "filing_crosscheck": {
                "verification_results": [
                    {"claim": "Revenue grew 12%", "status": "verified"}
                ],
                "consistency_score": 0.91,
                "flagged_discrepancies": [],
            },
        }

        report = asyncio.run(agent._generate_report(merged, {"ticker": "AMD"}))

        self.assertIn("AMD", report["executive_summary"])
        self.assertEqual(report["consistency_score"], 0.91)
        self.assertGreaterEqual(len(report["risk_factors"]), 0)
        self.assertIn("Revenue", report["full_report"])


if __name__ == "__main__":
    unittest.main()
