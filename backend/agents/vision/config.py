"""
Vision Agent Configuration
==========================
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VisionConfig(BaseModel):
    """Configuration for the Vision Analysis Agent."""

    # Model
    model_name: str = Field(
        default="Qwen/Qwen2.5-VL-7B-Instruct",
        description="Vision-Language model to use.",
    )
    device: str = "cuda"
    compute_type: str = "float16"
    max_new_tokens: int = Field(default=2048, ge=64)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # Slide processing
    max_slides: int = Field(
        default=100,
        description="Maximum number of slides to process.",
    )
    supported_formats: list[str] = Field(
        default=[".pdf", ".pptx", ".png", ".jpg", ".jpeg"],
    )
    dpi: int = Field(
        default=200,
        description="DPI for PDF-to-image rasterization.",
    )

    # Extraction targets
    extract_kpis: bool = True
    extract_charts: bool = True
    extract_tables: bool = True
    extract_guidance: bool = True
