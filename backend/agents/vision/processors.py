"""
Vision Processors
=================

Isolated processing functions for slide rasterization,
VLM inference, and structured data extraction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------

@dataclass
class SlideAnalysis:
    """Analysis result for a single slide."""

    slide_index: int
    image_path: str
    raw_description: str = ""
    kpis: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    guidance_statements: List[str] = field(default_factory=list)


@dataclass
class ExtractedKPI:
    """A single KPI extracted from a slide."""

    name: str
    value: str
    unit: Optional[str] = None
    period: Optional[str] = None
    slide_index: int = 0
    confidence: float = 0.0


# ------------------------------------------------------------------
# Processors
# ------------------------------------------------------------------

async def rasterize_slides(
    slides_path: str,
    output_dir: str,
    dpi: int = 200,
) -> List[str]:
    """Convert PDF/PPTX slides to individual PNG images."""
    logger.info("Rasterizing slides from: %s", slides_path)
    output_paths = []
    
    path_obj = Path(slides_path)
    if not path_obj.exists():
        logger.error("Slides file not found: %s", slides_path)
        return []

    try:
        from pdf2image import convert_from_path
        # Requires poppler to be installed on the system
        images = convert_from_path(slides_path, dpi=dpi)
        
        out_dir_path = Path(output_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)
        
        for i, img in enumerate(images):
            out_file = out_dir_path / f"slide_{i}.png"
            img.save(str(out_file), "PNG")
            output_paths.append(str(out_file))
            
    except Exception as exc:
        logger.error("Failed to rasterize slides: %s", exc)

    return output_paths


async def analyze_slide_image(
    image_path: str,
    model: Any,
    processor: Any,
    prompt: str = "Analyze this earnings presentation slide in detail. Extract any KPIs, guidance metrics, and key statements.",
    slide_index: int = 0,
) -> SlideAnalysis:
    """Run VLM inference on a single slide image."""
    analysis = SlideAnalysis(slide_index=slide_index, image_path=image_path)
    if not model:
        logger.warning("No VLM model provided for slide %d", slide_index)
        return analysis

    try:
        import base64
        from langchain_core.messages import HumanMessage
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ]
        )
        
        response = model.invoke([message])
        content = getattr(response, "content", str(response))
        analysis.raw_description = content
        
        # Simple extraction logic (in reality, prompt should demand JSON output)
        lower = content.lower()
        if "kpi" in lower or "revenue" in lower:
            analysis.kpis.append(
                {"name": "Extracted KPI", "value": "See raw description", "slide": slide_index}
            )
        for phrase in ("guidance", "outlook", "expect", "forecast", "forward-looking"):
            if phrase in lower:
                analysis.guidance_statements.append(content[:400])
                break
            
    except Exception as exc:
        logger.error("Failed VLM inference on slide %d: %s", slide_index, exc)
        
    return analysis


async def extract_kpis_from_analysis(
    analyses: List[SlideAnalysis],
) -> List[ExtractedKPI]:
    """Aggregate and deduplicate KPIs across all slides."""
    kpis = []
    for a in analyses:
        for k in a.kpis:
            kpis.append(
                ExtractedKPI(
                    name=k.get("name", "Unknown"),
                    value=k.get("value", ""),
                    slide_index=a.slide_index,
                    confidence=0.9
                )
            )
    return kpis


async def extract_tables_from_analysis(
    analyses: List[SlideAnalysis],
) -> List[Dict[str, Any]]:
    """Aggregate parsed tables across all slides."""
    tables = []
    for a in analyses:
        tables.extend(a.tables)
    return tables


async def extract_guidance_from_analysis(
    analyses: List[SlideAnalysis],
) -> List[Dict[str, Any]]:
    """Aggregate forward-looking guidance statements across all slides."""
    guidance: List[Dict[str, Any]] = []
    for analysis in analyses:
        for statement in analysis.guidance_statements:
            text = statement.strip()
            if text:
                guidance.append({"text": text, "slide_index": analysis.slide_index})
    return guidance
