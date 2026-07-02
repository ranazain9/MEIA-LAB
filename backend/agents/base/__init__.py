"""
Base Agent Module
=================

Abstract base class and shared interfaces for all MEIA agents.
"""

from backend.agents.base.base_agent import BaseAgent
from backend.agents.base.schemas import (
    AgentInput,
    AgentOutput,
    AgentStatus,
    HistoricalComparison,
    IntelligenceReport,
    KPIExtraction,
    SlideInsight,
    ToneSegment,
    TranscriptSegment,
    VerificationResult,
)
from backend.agents.base.exceptions import (
    AgentError,
    AgentTimeoutError,
    AgentProcessingError,
)

__all__ = [
    "BaseAgent",
    "AgentInput",
    "AgentOutput",
    "AgentStatus",
    "HistoricalComparison",
    "IntelligenceReport",
    "KPIExtraction",
    "SlideInsight",
    "ToneSegment",
    "TranscriptSegment",
    "VerificationResult",
    "AgentError",
    "AgentTimeoutError",
    "AgentProcessingError",
]
