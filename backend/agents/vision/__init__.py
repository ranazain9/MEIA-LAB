"""
Vision Analysis Agent
=====================

Slide deck analysis, KPI extraction, chart interpretation,
table understanding, and forward guidance extraction.

Models:
    - Qwen-VL
    - LLaVA
"""

from backend.agents.vision.agent import VisionAgent
from backend.agents.vision.config import VisionConfig

__all__ = ["VisionAgent", "VisionConfig"]
