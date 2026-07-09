"""
Orchestrator Agent Configuration
=================================
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class OrchestratorConfig(BaseModel):
    """Configuration for the Orchestrator & Report Agent."""

    # LLM
    llm_model: str = Field(
        default_factory=lambda: os.getenv("MEIA_LLM_MODEL", "openai/gpt-oss-safeguard-20b"),
        description="LLM for reasoning, synthesis, and report generation.",
    )
    llm_provider: str = Field(
        default_factory=lambda: os.getenv("MEIA_LLM_PROVIDER", "groq"),
        description="LangChain provider for the reasoning model (groq/aimlapi/openai/hf/local).",
    )
    device: str = "cuda"
    max_new_tokens: int = Field(default=4096, ge=128)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # Orchestration
    parallel_agents: bool = Field(
        default=True,
        description="Run independent agents (ASR, Vision, Filing) in parallel.",
    )
    agent_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("MEIA_AGENT_TIMEOUT_SECONDS", "120")),
        description="Max time to wait for a single agent to finish.",
    )
    max_retries: int = Field(default=2, ge=0)

    # Report
    report_format: str = Field(
        default="markdown",
        description="Output format: 'markdown', 'json', 'pdf'.",
    )
    include_executive_summary: bool = True
    include_tone_analysis: bool = True
    include_risk_detection: bool = True
    include_slide_comparison: bool = True
    include_historical: bool = True

    # LangGraph
    langgraph_checkpoint_dir: str = "./data/langgraph_checkpoints"
