"""
Vision Agent Implementation
===========================

Processes earnings presentation slides through a Vision-Language Model
to extract KPIs, interpret charts, parse tables, and identify guidance.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import os
from backend.agents.base import BaseAgent, AgentInput, AgentOutput
from backend.agents.vision.config import VisionConfig

logger = logging.getLogger(__name__)


class VisionAgent(BaseAgent):
    """
    Agent 2 — Vision Analysis.

    Pipeline:
        slides → rasterize → per-slide VLM inference → structured extraction
    """

    AGENT_NAME = "vision_analysis"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._vision_config = VisionConfig(**(config or {}))
        self._model = None
        self._processor = None

    @property
    def agent_name(self) -> str:
        return self.AGENT_NAME

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _initialize_impl(self) -> None:
        """Load VLM onto GPU."""
        logger.info(
            "Vision Agent: loading model=%s device=%s",
            self._vision_config.model_name,
            self._vision_config.device,
        )
        import os
        from backend.agents.langchain_utils import build_llm

        try:
            provider = os.getenv("MEIA_VISION_LLM_PROVIDER", os.getenv("MEIA_LLM_PROVIDER", "groq"))
            model_name = os.getenv("MEIA_VISION_MODEL", self._vision_config.model_name)
            self._model = build_llm(
                model_name=model_name,
                temperature=self._vision_config.temperature,
                provider=provider,
            )
        except Exception as exc:
            logger.error("Failed to initialize Vision LLM: %s", exc)
    async def _process_impl(self, agent_input: AgentInput) -> AgentOutput:
        """
        Analyze slide deck images.

        Expected input payload keys:
            - slides_path (str): Path to PDF/PPTX or directory of images.

        Returns AgentOutput with data keys:
            - slides (list[dict]): Per-slide analysis results.
            - kpis (list[dict]): Extracted key performance indicators.
            - charts (list[dict]): Chart descriptions and data points.
            - tables (list[dict]): Parsed table contents.
            - guidance (list[dict]): Forward-looking statements.
        """
        slides_path = agent_input.payload.get("slides_path")
        if not slides_path:
            return AgentOutput(
                request_id=agent_input.request_id,
                agent_name=self.agent_name,
                success=False,
                errors=["Missing required field: slides_path"],
            )

        try:
            import shutil
            import tempfile
            from backend.agents.vision.processors import (
                analyze_slide_image,
                extract_guidance_from_analysis,
                extract_kpis_from_analysis,
                extract_tables_from_analysis,
                rasterize_slides,
            )
            from backend.agents.vision.utils import resize_for_vlm

            temp_dir = tempfile.mkdtemp()
            try:
                try:
                    image_paths = await rasterize_slides(
                        slides_path=slides_path,
                        output_dir=temp_dir,
                        dpi=self._vision_config.dpi,
                    )
                except Exception:
                    logger.exception(
                        "Slide extraction failed",
                        extra={"file": slides_path, "stage": "SLIDE_RASTERIZATION"},
                    )
                    image_paths = []

                import asyncio
                # Gather batch size configuration from environment
                batch_size = int(os.getenv("MEIA_GROQ_BATCH_SIZE", "4"))
                
                # Resize all slide images first
                resized_paths = []
                for i, img_path in enumerate(image_paths[: self._vision_config.max_slides]):
                    try:
                        resized_path = resize_for_vlm(img_path)
                    except Exception:
                        logger.exception(
                            "Slide resize failed",
                            extra={"file": img_path, "stage": "SLIDE_RASTERIZATION"},
                        )
                        resized_path = img_path
                    resized_paths.append((i, resized_path))

                # Batch the slide images
                batches = [resized_paths[j:j + batch_size] for j in range(0, len(resized_paths), batch_size)]
                
                # Submit batches to QueueWorkerPool
                from backend.core.queue_worker import QueueWorkerPool
                from backend.agents.vision.processors import analyze_slide_batch
                
                pool = QueueWorkerPool(worker_count=int(os.getenv("MEIA_GROQ_WORKERS", "2")))
                
                tasks = []
                for b_idx, batch in enumerate(batches):
                    task = pool.submit(
                        analyze_slide_batch,
                        batch=batch,
                        model=self._model,
                        batch_index=b_idx,
                        total_batches=len(batches)
                    )
                    tasks.append(task)
                
                # Wait for all tasks to complete
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Shut down the pool workers
                await pool.shutdown()
                
                # Gather SlideAnalysis results
                analyses = []
                for res in batch_results:
                    if isinstance(res, list):
                        analyses.extend(res)
                    elif isinstance(res, Exception):
                        logger.error("Batch task failed: %s", res)
                
                # Sort analyses by slide_index to maintain correct order
                analyses.sort(key=lambda x: x.slide_index)


                kpis = await extract_kpis_from_analysis(analyses)
                tables = await extract_tables_from_analysis(analyses)
                guidance = await extract_guidance_from_analysis(analyses)

                slides_data = [a.__dict__ if hasattr(a, "__dict__") else {} for a in analyses]
                kpis_data = [k.__dict__ if hasattr(k, "__dict__") else {} for k in kpis]
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception:
            logger.exception(
                "Vision pipeline failed",
                extra={"file": slides_path, "stage": "SLIDE_RASTERIZATION"},
            )
            slides_data = []
            kpis_data = []
            tables = []
            guidance = []

        return AgentOutput(
            request_id=agent_input.request_id,
            agent_name=self.agent_name,
            success=True,
            data={
                "slides": slides_data,
                "kpis": kpis_data,
                "charts": [
                    chart
                    for slide in slides_data
                    for chart in slide.get("charts", [])
                ],
                "tables": tables,
                "guidance": guidance,
            },
        )

    async def _shutdown_impl(self) -> None:
        self._model = None
        self._processor = None
        logger.info("Vision Agent: models unloaded.")
