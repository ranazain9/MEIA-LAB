"""
ASR Agent Implementation
========================

Orchestrates Whisper transcription, WhisperX alignment,
speaker diarization, and tone analysis.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.agents.base import BaseAgent, AgentInput, AgentOutput
from backend.agents.asr.config import ASRConfig

logger = logging.getLogger(__name__)


class ASRAgent(BaseAgent):
    """
    Agent 1 — ASR & Alignment.

    Pipeline:
        audio → transcription → alignment → diarization → tone analysis
    """

    AGENT_NAME = "asr_alignment"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._asr_config = ASRConfig(**(config or {}))
        self._model = None
        self._align_model = None

    @property
    def agent_name(self) -> str:
        return self.AGENT_NAME

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _initialize_impl(self) -> None:
        """Initialize the Groq client for transcription."""
        import os
        from groq import AsyncGroq
        api_key = self._asr_config.groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY is not set. ASR transcription will fail.")
        self._model = AsyncGroq(api_key=api_key)
        logger.info("ASR Agent: Groq client initialized using whisper-large-v3 model.")



    async def _process_impl(self, agent_input: AgentInput) -> AgentOutput:
        """
        Run the full ASR pipeline.

        Expected input payload keys:
            - audio_path (str): Path to the earnings call audio file.
            - slides_timestamps (list[float], optional): Slide change timestamps.

        Returns AgentOutput with data keys:
            - transcript (list[dict]): Segments with text, start, end, speaker.
            - tone_analysis (list[dict]): Per-window energy and sentiment.
            - slide_alignment (list[dict]): Mapping of slides → transcript ranges.
        """
        audio_path = agent_input.payload.get("audio_path")
        if not audio_path:
            return AgentOutput(
                request_id=agent_input.request_id,
                agent_name=self.agent_name,
                success=False,
                errors=["Missing required field: audio_path"],
            )

        try:
            from backend.agents.asr.processors import (
                transcribe_audio,
                align_transcript,
                diarize_speakers,
                analyze_tone,
                align_slides_to_transcript,
            )

            # Step 1: Transcription
            try:
                segments = await transcribe_audio(
                    audio_path=audio_path,
                    model=self._model,
                    language=self._asr_config.language,
                    batch_size=self._asr_config.batch_size
                )
            except Exception:
                logger.exception(
                    "Audio transcription failed",
                    extra={"file": audio_path, "stage": "ASR"},
                )
                segments = []

            # Step 2: Alignment (Using basic whisper timestamps for now instead of whisperx)
            segments = await align_transcript(segments, audio_path, None)

            # Step 3: Diarization
            if self._asr_config.enable_diarization:
                segments = await diarize_speakers(
                    segments=segments,
                    audio_path=audio_path,
                    min_speakers=self._asr_config.min_speakers,
                    max_speakers=self._asr_config.max_speakers
                )

            # Step 4: Tone Analysis
            tone_windows = []
            if self._asr_config.enable_tone_analysis:
                tone_windows = await analyze_tone(audio_path, segments)

            # Step 5: Slide Alignment
            slide_timestamps = agent_input.payload.get("slide_timestamps", [])
            slide_alignments = await align_slides_to_transcript(segments, slide_timestamps)

            # Format data for output
            transcript_data = [s.__dict__ if hasattr(s, "__dict__") else {} for s in segments]
            tone_data = [t.__dict__ if hasattr(t, "__dict__") else {} for t in tone_windows]
            alignment_data = []
            for sa in slide_alignments:
                sa_dict = {"slide_index": sa.slide_index, "start": sa.slide_start, "end": sa.slide_end}
                sa_dict["segments"] = [s.__dict__ if hasattr(s, "__dict__") else {} for s in sa.segments]
                alignment_data.append(sa_dict)

        except Exception as exc:
            logger.exception(
                "ASR pipeline failed",
                extra={"file": audio_path, "stage": "ASR"},
            )
            return AgentOutput(
                request_id=agent_input.request_id,
                agent_name=self.agent_name,
                success=False,
                errors=[str(exc)],
            )

        return AgentOutput(
            request_id=agent_input.request_id,
            agent_name=self.agent_name,
            success=True,
            data={
                "transcript": transcript_data,
                "tone_analysis": tone_data,
                "slide_alignment": alignment_data,
            },
        )

    async def _shutdown_impl(self) -> None:
        """Unload models and free GPU memory."""
        self._model = None
        self._align_model = None
        logger.info("ASR Agent: models unloaded.")
