"""
Filing Processors
=================

Functions for SEC EDGAR interaction, document chunking,
embedding, and numerical verification.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.agents.filing.sec_client import (
    fetch_filing_document,
    fetch_submissions,
    iter_recent_filings,
    lookup_cik,
)

logger = logging.getLogger(__name__)

_METRIC_PATTERNS = {
    "Revenue": re.compile(
        r"(?:total\s+)?revenues?[^$\n]{0,60}?\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?",
        re.IGNORECASE,
    ),
    "EPS": re.compile(
        r"(?:earnings\s+per\s+share|diluted\s+eps|basic\s+eps)[^$\n]{0,40}?\$\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
}


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------

@dataclass
class SECFiling:
    """Metadata and content of a retrieved SEC filing."""

    filing_type: str
    filed_date: str
    accession_number: str
    company_name: str
    ticker: str
    content: str = ""
    url: str = ""


@dataclass
class VerificationResult:
    """Result of verifying a single numerical claim."""

    claim_text: str
    claimed_value: str
    filing_value: Optional[str] = None
    is_consistent: bool = False
    confidence: float = 0.0
    source_filing: Optional[str] = None
    evidence_snippet: str = ""


@dataclass
class HistoricalComparison:
    """Quarter-over-quarter or year-over-year comparison."""

    metric: str
    current_value: float
    previous_value: float
    delta: float = 0.0
    delta_pct: float = 0.0
    period_current: str = ""
    period_previous: str = ""


# ------------------------------------------------------------------
# Processors
# ------------------------------------------------------------------

async def fetch_sec_filings(
    ticker: str,
    filing_types: List[str],
    max_filings: int = 8,
    user_agent: str = "MEIA-LAB meia@example.com",
) -> List[SECFiling]:
    """Retrieve real filings from SEC EDGAR submissions API."""
    logger.info("Fetching SEC filings for %s", ticker)
    filings: List[SECFiling] = []

    try:
        import httpx

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            cik = await lookup_cik(ticker, client, user_agent=user_agent)
            if not cik:
                logger.warning("No CIK found for ticker %s", ticker)
                return filings

            submissions = await fetch_submissions(cik, client, user_agent=user_agent)
            company_name = submissions.get("name", ticker.upper())
            candidates = iter_recent_filings(submissions, filing_types, max_filings)

            for item in candidates:
                try:
                    content = await fetch_filing_document(
                        cik,
                        item["accession_number"],
                        item["primary_document"],
                        client,
                        user_agent=user_agent,
                    )
                except Exception as exc:
                    logger.warning(
                        "Skipping filing %s: %s",
                        item["accession_number"],
                        exc,
                    )
                    continue

                if not content:
                    continue

                url = (
                    f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                    f"{item['accession_number'].replace('-', '')}/"
                    f"{item['primary_document']}"
                )
                filings.append(
                    SECFiling(
                        filing_type=item["filing_type"],
                        filed_date=item["filed_date"],
                        accession_number=item["accession_number"],
                        company_name=company_name,
                        ticker=ticker.upper(),
                        content=content[:500_000],
                        url=url,
                    )
                )

            logger.info("Retrieved %d SEC filings for %s", len(filings), ticker)
    except Exception as exc:
        logger.error("Failed to fetch SEC filings: %s", exc)

    return filings


def _parse_metric_value(raw: str, unit: str = "") -> Optional[float]:
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        return None
    unit_lower = unit.lower()
    if unit_lower == "billion":
        value *= 1_000
    return value


def _extract_metric_from_text(metric: str, text: str) -> Optional[float]:
    pattern = _METRIC_PATTERNS.get(metric)
    if not pattern:
        return None
    match = pattern.search(text)
    if not match:
        return None
    unit = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
    return _parse_metric_value(match.group(1), unit or "")


async def chunk_filing_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[str]:
    """Split filing text into overlapping chunks for embedding."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return splitter.split_text(text)
    except Exception as exc:
        logger.error("Failed to chunk text: %s", exc)
        return [text]


async def embed_and_store(
    chunks: List[str],
    metadata: Dict[str, Any],
    collection: Any,
    embedding_model: Any,
) -> None:
    """Embed text chunks and upsert into ChromaDB."""
    if not collection:
        logger.warning("No ChromaDB collection provided.")
        return

    metadatas = [metadata for _ in chunks]
    try:
        collection.add_texts(texts=chunks, metadatas=metadatas)
        logger.info("Added %d chunks to ChromaDB", len(chunks))
    except Exception as exc:
        logger.error("Failed to add texts to ChromaDB: %s", exc)


def _claim_matches_evidence(claimed_value: str, evidence: str) -> bool:
    if not evidence:
        return False
    if claimed_value and claimed_value.lower() in evidence.lower():
        return True
    numbers = re.findall(r"\d+(?:\.\d+)?", claimed_value)
    return any(number in evidence for number in numbers if len(number) >= 2)


async def verify_claim(
    claim: Dict[str, Any],
    collection: Any,
    embedding_model: Any,
    top_k: int = 5,
) -> VerificationResult:
    """Verify a numerical claim against stored filing chunks."""
    claim_text = claim.get("text", "")
    claimed_value = claim.get("value", "")

    if not collection:
        return VerificationResult(
            claim_text=claim_text,
            claimed_value=claimed_value,
        )

    try:
        docs = collection.similarity_search(claim_text, k=top_k)
        evidence = docs[0].page_content if docs else ""
        source = docs[0].metadata.get("source") if docs else None
        is_consistent = _claim_matches_evidence(claimed_value, evidence)

        return VerificationResult(
            claim_text=claim_text,
            claimed_value=claimed_value,
            filing_value=claimed_value if is_consistent else None,
            is_consistent=is_consistent,
            confidence=0.85 if is_consistent else 0.25,
            source_filing=source,
            evidence_snippet=evidence[:500],
        )
    except Exception as exc:
        logger.error("Failed to verify claim: %s", exc)
        return VerificationResult(
            claim_text=claim_text,
            claimed_value=claimed_value,
        )


async def compute_historical_comparison(
    filings: List[SECFiling],
    metrics: List[str],
) -> List[HistoricalComparison]:
    """Compute metric deltas across the two most recent filings."""
    comparisons: List[HistoricalComparison] = []
    if len(filings) < 1:
        return comparisons

    ordered = sorted(filings, key=lambda filing: filing.filed_date, reverse=True)
    current = ordered[0]
    previous = ordered[1] if len(ordered) > 1 else None

    for metric in metrics:
        current_value = _extract_metric_from_text(metric, current.content)
        previous_value = (
            _extract_metric_from_text(metric, previous.content) if previous else None
        )
        if current_value is None:
            continue

        prev = previous_value if previous_value is not None else current_value
        delta = current_value - prev
        delta_pct = (delta / prev * 100.0) if prev else 0.0
        comparisons.append(
            HistoricalComparison(
                metric=metric,
                current_value=current_value,
                previous_value=prev,
                delta=round(delta, 4),
                delta_pct=round(delta_pct, 2),
                period_current=current.filed_date,
                period_previous=previous.filed_date if previous else current.filed_date,
            )
        )

    return comparisons
