"""
Vision Processors
=================

Isolated processing functions for slide rasterization,
VLM inference, and structured data extraction.
"""

from __future__ import annotations

import logging
import textwrap
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
    """Convert PDF slides to individual PNG images using PyMuPDF."""
    logger.info("Rasterizing slides from: %s", slides_path)
    output_paths = []
    
    path_obj = Path(slides_path)
    if not path_obj.exists():
        logger.error(
            "Slides file not found",
            extra={"file": slides_path, "stage": "SLIDE_RASTERIZATION"},
        )
        return []

    try:
        out_dir_path = Path(output_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)

        if path_obj.is_dir():
            from backend.agents.vision.utils import collect_slide_images

            return [str(path) for path in collect_slide_images(str(path_obj))]

        if path_obj.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
            return [str(path_obj)]

        if path_obj.suffix.lower() != ".pdf":
            raise ValueError(f"Unsupported slide format: {path_obj.suffix}")

        import fitz

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        with fitz.open(str(path_obj)) as document:
            for i, page in enumerate(document):
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                out_file = out_dir_path / f"slide_{i}.png"
                pixmap.save(str(out_file))
                output_paths.append(str(out_file))

    except Exception:
        logger.exception(
            "Slide rasterization failed",
            extra={"file": slides_path, "stage": "SLIDE_RASTERIZATION"},
        )
        output_paths = await _fallback_rasterize_slides(path_obj, output_dir)

    return output_paths


async def _fallback_rasterize_slides(path_obj: Path, output_dir: str) -> List[str]:
    """Create simple placeholder slide images when PDF rasterization is unavailable."""
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    page_texts: List[str] = []
    if path_obj.suffix.lower() == ".pdf":
        try:
            import fitz

            with fitz.open(str(path_obj)) as document:
                for page in document:
                    extracted = page.get_text("text") or ""
                    page_texts.append(extracted.strip())
        except Exception:
            logger.exception(
                "PDF text fallback failed",
                extra={"file": str(path_obj), "stage": "SLIDE_RASTERIZATION"},
            )

    if not page_texts:
        page_texts = [f"Unable to rasterize {path_obj.name}."]

    output_paths: List[str] = []
    for index, text in enumerate(page_texts):
        image_path = out_dir_path / f"slide_{index}.png"
        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 1280, 960
            image = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            wrapped = "\n".join(textwrap.wrap(text[:4000] or "No slide text extracted.", width=90))
            draw.multiline_text((48, 48), wrapped, fill="black", font=font, spacing=6)
            image.save(image_path, "PNG")
            output_paths.append(str(image_path))
        except Exception:
            logger.exception(
                "Fallback slide image generation failed",
                extra={"file": str(path_obj), "stage": "SLIDE_RASTERIZATION"},
            )

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


async def analyze_slide_batch(
    batch: List[Tuple[int, str]],
    model: Any,
    batch_index: int,
    total_batches: int,
    prompt: str = "Analyze these earnings presentation slides. Extract any KPIs, guidance metrics, and key statements for each slide.",
) -> List[SlideAnalysis]:
    """Run VLM inference on a batch of slide images and return structured JSON for each slide."""
    logger.info("[Groq] batch %d/%d", batch_index + 1, total_batches)
    analyses = []
    
    # Initialize empty analyses for the batch in case of failures
    for slide_idx, img_path in batch:
        analyses.append(SlideAnalysis(slide_index=slide_idx, image_path=img_path))
        
    if not model:
        logger.warning("No VLM model provided for batch %d", batch_index)
        return analyses

    try:
        import base64
        import json
        from langchain_core.messages import HumanMessage
        
        # Load and base64-encode all images in the batch
        content_list = []
        
        # Instruction prompt demanding JSON response
        system_instruction = (
            f"You are analyzing a batch of earnings presentation slides: {[idx for idx, _ in batch]}.\n"
            "Analyze each slide in detail. Extract any KPIs (period, name, value, unit), guidance metrics (statements), and tables.\n"
            "Return the output strictly as a JSON object with a key 'slides' which contains a list of slide analysis objects.\n"
            "Each slide object must strictly match this JSON schema:\n"
            "{\n"
            "  \"slide_index\": int,\n"
            "  \"raw_description\": \"A detailed textual summary of the slide contents\",\n"
            "  \"kpis\": [{\"name\": \"...\", \"value\": \"...\", \"unit\": \"...\", \"period\": \"...\"}],\n"
            "  \"guidance_statements\": [\"...\"],\n"
            "  \"tables\": [{\"table_title\": \"...\", \"rows\": [...]}]\n"
            "}\n"
            "Ensure that every slide in the batch gets a matching object in the list."
        )
        content_list.append({"type": "text", "text": system_instruction})
        
        for slide_idx, img_path in batch:
            with open(img_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            content_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            })
            
        message = HumanMessage(content=content_list)
        
        # Call the model (our CentralizedGroqChatModel will route it through groq_client.chat)
        response = model.invoke([message], response_format={"type": "json_object"})
        raw_content = getattr(response, "content", str(response)).strip()
        
        # Parse structured JSON from response
        try:
            data = json.loads(raw_content)
            slides_json = data.get("slides") or []
            
            # Map the parsed JSON back to SlideAnalysis objects
            mapped_analyses = []
            for slide_idx, img_path in batch:
                # Find matching index in JSON
                match = None
                for sj in slides_json:
                    if sj.get("slide_index") == slide_idx:
                        match = sj
                        break
                
                analysis = SlideAnalysis(slide_index=slide_idx, image_path=img_path)
                if match:
                    analysis.raw_description = match.get("raw_description") or ""
                    analysis.kpis = match.get("kpis") or []
                    analysis.guidance_statements = match.get("guidance_statements") or []
                    analysis.tables = match.get("tables") or []
                else:
                    logger.warning("No JSON match found for slide index %d in batch response", slide_idx)
                
                mapped_analyses.append(analysis)
            
            return mapped_analyses
            
        except Exception as json_exc:
            logger.error("Failed to parse JSON response in batch %d: %s. Raw content: %s", batch_index, json_exc, raw_content)
            # Fall back to raw description
            for a in analyses:
                a.raw_description = raw_content
            
    except Exception as exc:
        logger.error("Failed VLM inference on batch %d: %s", batch_index, exc)
        
    return analyses



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
