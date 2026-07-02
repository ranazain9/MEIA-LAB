import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.filing.processors import (
    _claim_matches_evidence,
    compute_historical_comparison,
    fetch_sec_filings,
)
from backend.agents.filing.sec_client import (
    html_to_text,
    iter_recent_filings,
    lookup_cik,
    reset_ticker_cache,
)


class SECClientTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_ticker_cache()

    def test_html_to_text_strips_tags(self):
        text = html_to_text("<html><body><p>Revenue $12 billion</p></body></html>")
        self.assertIn("Revenue", text)
        self.assertNotIn("<p>", text)

    def test_iter_recent_filings_filters_form_types(self):
        submissions = {
            "filings": {
                "recent": {
                    "form": ["10-K", "4", "10-Q"],
                    "filingDate": ["2025-01-01", "2025-01-02", "2025-04-01"],
                    "accessionNumber": ["a1", "a2", "a3"],
                    "primaryDocument": ["k.htm", "4.xml", "q.htm"],
                }
            }
        }
        matches = iter_recent_filings(submissions, ["10-K", "10-Q"], max_filings=5)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["filing_type"], "10-K")

    def test_claim_matches_evidence(self):
        self.assertTrue(_claim_matches_evidence("12%", "Revenue grew 12% year over year"))
        self.assertFalse(_claim_matches_evidence("99%", "Revenue grew 12% year over year"))

    def test_compute_historical_comparison_from_filings(self):
        filings = [
            MagicMock(
                filed_date="2025-04-01",
                content="Total revenue $ 5,000 million for the quarter.",
            ),
            MagicMock(
                filed_date="2025-01-01",
                content="Total revenue $ 4,800 million for the quarter.",
            ),
        ]
        comparisons = asyncio.run(
            compute_historical_comparison(filings, ["Revenue"])
        )
        self.assertEqual(len(comparisons), 1)
        self.assertGreater(comparisons[0].current_value, comparisons[0].previous_value)

    @patch("backend.agents.filing.processors.fetch_filing_document", new_callable=AsyncMock)
    @patch("backend.agents.filing.processors.fetch_submissions", new_callable=AsyncMock)
    @patch("backend.agents.filing.processors.lookup_cik", new_callable=AsyncMock)
    def test_fetch_sec_filings_uses_edgar_pipeline(
        self,
        mock_lookup,
        mock_submissions,
        mock_document,
    ):
        mock_lookup.return_value = "2488"
        mock_submissions.return_value = {
            "name": "ADVANCED MICRO DEVICES INC",
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["2025-02-05"],
                    "accessionNumber": ["0000002488-25-000001"],
                    "primaryDocument": ["amd-20241228.htm"],
                }
            },
        }
        mock_document.return_value = "<html><body>Total revenue $ 25,000 million</body></html>"

        filings = asyncio.run(fetch_sec_filings("AMD", ["10-K"], max_filings=1))

        self.assertEqual(len(filings), 1)
        self.assertEqual(filings[0].ticker, "AMD")
        self.assertIn("revenue", filings[0].content.lower())

    @patch("backend.agents.filing.sec_client.load_ticker_map", new_callable=AsyncMock)
    def test_lookup_cik_reads_cache(self, mock_load):
        async def _load(_client, user_agent=None):
            from backend.agents.filing import sec_client

            sec_client._TICKER_TO_CIK["AMD"] = "2488"
            return sec_client._TICKER_TO_CIK

        mock_load.side_effect = _load
        cik = asyncio.run(lookup_cik("AMD", MagicMock()))
        self.assertEqual(cik, "2488")


if __name__ == "__main__":
    unittest.main()
