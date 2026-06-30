"""
Filing Utilities
================

Helpers for SEC EDGAR URL construction, CIK lookup,
and financial number parsing.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


EDGAR_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start}&enddt={end}"
EDGAR_FILING_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}"


def normalize_ticker(ticker: str) -> str:
    """Normalize a ticker symbol to uppercase, stripped."""
    return ticker.strip().upper()


def parse_financial_number(text: str) -> Optional[float]:
    """
    Parse a financial number string into a float.

    Handles formats like:
        "$1.2B", "$450M", "1,234,567", "$12.5 million", "(3.2%)"
    """
    text = text.strip().replace(",", "").replace("$", "")

    multipliers = {
        "t": 1e12, "trillion": 1e12,
        "b": 1e9, "billion": 1e9,
        "m": 1e6, "million": 1e6,
        "k": 1e3, "thousand": 1e3,
    }

    for suffix, mult in multipliers.items():
        pattern = rf"([\d.]+)\s*{suffix}"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1)) * mult

    # Plain number
    match = re.search(r"[-+]?[\d.]+", text)
    if match:
        return float(match.group())

    return None


def build_edgar_search_url(
    ticker: str,
    filing_type: str = "10-K",
) -> str:
    """Construct an SEC EDGAR full-text search URL."""
    return (
        f"https://efts.sec.gov/LATEST/search-index"
        f"?q=%22{ticker}%22&forms={filing_type}"
    )
