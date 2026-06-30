"""
Orchestrator Processors
=======================

Prompt templates, report formatters, and risk detection logic
used by the Orchestrator Agent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------

@dataclass
class RiskFactor:
    """A detected risk or anomaly."""

    category: str           # e.g. "numerical_discrepancy", "tone_shift"
    description: str
    severity: str = "medium"
    evidence: str = ""
    source_agent: str = ""


@dataclass
class ReportSection:
    """A named section of the Analyst Intelligence Brief."""

    title: str
    content: str
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Prompt templates
# ------------------------------------------------------------------

EXECUTIVE_SUMMARY_PROMPT = """You are a senior financial analyst. Based on the following multimodal analysis of a corporate earnings call, write a concise three-sentence executive summary.

Transcript Analysis:
{transcript_summary}

Slide Analysis:
{slide_summary}

Filing Verification:
{filing_summary}

Executive Summary:"""

RISK_DETECTION_PROMPT = """Analyze the following earnings call data for potential risks, anomalies, and concerns. Identify discrepancies between spoken statements and official filings, tone shifts, and any unusual patterns.

Data:
{merged_data}

List each risk factor with category, description, severity (low/medium/high/critical), and evidence:"""

REPORT_SYNTHESIS_PROMPT = """Generate a comprehensive Analyst Intelligence Brief from the following earnings call analysis.

Include sections:
1. Executive Summary
2. Tone & Sentiment Analysis
3. Key Financial Metrics
4. Numerical Consistency Assessment
5. Risk Factors
6. Slide-to-Speech Comparison
7. Historical Performance
8. Analyst Recommendations

Analysis Data:
{merged_data}

Analyst Intelligence Brief:"""


# ------------------------------------------------------------------
# Processors
# ------------------------------------------------------------------

async def detect_risks(
    merged_data: Dict[str, Any],
    llm: Any = None,
) -> List[RiskFactor]:
    """Identify risks and anomalies from combined agent outputs."""
    # TODO: Implement risk detection logic + optional LLM call
    return []


async def format_report_markdown(
    sections: List[ReportSection],
) -> str:
    """Assemble report sections into a formatted Markdown document."""
    lines = ["# Analyst Intelligence Brief", ""]
    for section in sorted(sections, key=lambda s: s.order):
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.content)
        lines.append("")
    return "\n".join(lines)


async def format_report_json(
    sections: List[ReportSection],
) -> Dict[str, Any]:
    """Assemble report sections into a structured JSON payload."""
    return {
        section.title: {
            "content": section.content,
            "metadata": section.metadata,
        }
        for section in sorted(sections, key=lambda s: s.order)
    }
