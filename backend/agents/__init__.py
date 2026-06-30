"""
MEIA Agents Package
===================

Production-grade multi-agent system for earnings intelligence analysis.

Agents:
    - ASR Agent: Speech recognition, alignment, and tone analysis
    - Vision Agent: Slide deck analysis and KPI extraction
    - Filing Agent: SEC filing cross-check and verification
    - Orchestrator Agent: Agent coordination and report generation
"""

from backend.agents.registry import AgentRegistry

__all__ = [
    "AgentRegistry",
]
