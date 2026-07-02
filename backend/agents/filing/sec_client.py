"""
SEC EDGAR Client
================

Real SEC data access via the public EDGAR APIs.
https://www.sec.gov/search/edgar/aboutaccess
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_TICKER_TO_CIK: Dict[str, str] = {}
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVES_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
)


def edgar_user_agent() -> str:
    """SEC requires a descriptive User-Agent with contact info."""
    return os.getenv(
        "SEC_EDGAR_USER_AGENT",
        os.getenv("MEIA_EDGAR_USER_AGENT", "MEIA-LAB meia@example.com"),
    )


def edgar_headers(user_agent: Optional[str] = None) -> Dict[str, str]:
    return {
        "User-Agent": user_agent or edgar_user_agent(),
        "Accept-Encoding": "gzip, deflate",
    }


async def load_ticker_map(client: Any, user_agent: Optional[str] = None) -> Dict[str, str]:
    """Load and cache ticker → CIK mapping from SEC."""
    global _TICKER_TO_CIK
    if _TICKER_TO_CIK:
        return _TICKER_TO_CIK

    response = await client.get(_COMPANY_TICKERS_URL, headers=edgar_headers(user_agent))
    response.raise_for_status()
    payload = response.json()

    for entry in payload.values():
        ticker = str(entry.get("ticker", "")).upper()
        cik = str(entry.get("cik_str", "")).strip()
        if ticker and cik:
            _TICKER_TO_CIK[ticker] = cik

    logger.info("Loaded %d ticker → CIK mappings from SEC", len(_TICKER_TO_CIK))
    return _TICKER_TO_CIK


async def lookup_cik(
    ticker: str,
    client: Any,
    user_agent: Optional[str] = None,
) -> Optional[str]:
    """Resolve a stock ticker to a SEC CIK."""
    await load_ticker_map(client, user_agent=user_agent)
    return _TICKER_TO_CIK.get(ticker.upper())


def pad_cik(cik: str) -> str:
    return str(cik).zfill(10)


def accession_folder(accession_number: str) -> str:
    return accession_number.replace("-", "")


def html_to_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "head", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


async def fetch_submissions(
    cik: str,
    client: Any,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    url = _SUBMISSIONS_URL.format(cik=pad_cik(cik))
    response = await client.get(url, headers=edgar_headers(user_agent))
    response.raise_for_status()
    return response.json()


def iter_recent_filings(
    submissions: Dict[str, Any],
    filing_types: List[str],
    max_filings: int,
) -> List[Dict[str, str]]:
    """Extract recent filings matching requested form types."""
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    allowed = {form.upper() for form in filing_types}
    matches: List[Dict[str, str]] = []

    for form, filed_date, accession, primary_doc in zip(
        forms, dates, accessions, primary_docs
    ):
        if str(form).upper() not in allowed:
            continue
        matches.append(
            {
                "filing_type": str(form),
                "filed_date": str(filed_date),
                "accession_number": str(accession),
                "primary_document": str(primary_doc),
            }
        )
        if len(matches) >= max_filings:
            break

    return matches


async def fetch_filing_document(
    cik: str,
    accession_number: str,
    primary_document: str,
    client: Any,
    user_agent: Optional[str] = None,
) -> str:
    """Download a filing document and return plain text."""
    url = _ARCHIVES_URL.format(
        cik=int(cik),
        accession=accession_folder(accession_number),
        document=primary_document,
    )
    response = await client.get(url, headers=edgar_headers(user_agent), timeout=60.0)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    body = response.text

    if "html" in content_type or body.lstrip().startswith("<"):
        return html_to_text(body)
    return body


def reset_ticker_cache() -> None:
    """Clear cached ticker map (for tests)."""
    global _TICKER_TO_CIK
    _TICKER_TO_CIK = {}
