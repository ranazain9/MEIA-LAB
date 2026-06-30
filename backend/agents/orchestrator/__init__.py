"""
Orchestrator & Report Agent
============================

Coordinates all agents, synthesizes outputs,
performs risk assessment, and generates the final
Analyst Intelligence Brief.

Stack:
    - Llama 3.1
    - LangGraph agent workflow
"""

from backend.agents.orchestrator.agent import OrchestratorAgent
from backend.agents.orchestrator.config import OrchestratorConfig

__all__ = ["OrchestratorAgent", "OrchestratorConfig"]
