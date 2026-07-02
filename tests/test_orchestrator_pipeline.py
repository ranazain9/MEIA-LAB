import unittest

from backend.agents.orchestrator.pipeline import extract_claims_from_outputs, kpi_label


class PipelineClaimTests(unittest.TestCase):
    def test_extract_claims_from_kpis_and_transcript(self):
        claims = extract_claims_from_outputs(
            {
                "transcript": [
                    {"text": "Revenue grew 12% year over year in the quarter."},
                ],
            },
            {
                "kpis": [{"name": "Revenue", "value": "12%"}],
            },
        )

        self.assertGreaterEqual(len(claims), 1)
        self.assertTrue(any(c["source"] == "slide" for c in claims))

    def test_kpi_label_supports_name_and_label(self):
        self.assertEqual(kpi_label({"name": "EPS"}), "EPS")
        self.assertEqual(kpi_label({"label": "Revenue"}), "Revenue")


if __name__ == "__main__":
    unittest.main()
