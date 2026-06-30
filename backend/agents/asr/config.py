"""
ASR Agent Configuration
=======================

All configurable knobs for the ASR & Alignment Agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ASRConfig(BaseModel):
    """Configuration for the ASR & Alignment Agent."""

    # Model settings
    whisper_model: str = Field(
        default="large-v3",
        description="Whisper model variant to load.",
    )
    device: str = Field(
        default="cuda",
        description="Compute device (cuda / cpu).",
    )
    compute_type: str = Field(
        default="float16",
        description="Precision for inference (float16 / int8 / float32).",
    )

    # Transcription
    language: str | None = Field(
        default=None,
        description="Force a specific language code (e.g. 'en'). None = auto-detect.",
    )
    batch_size: int = Field(default=16, ge=1)

    # Diarization
    enable_diarization: bool = True
    min_speakers: int | None = None
    max_speakers: int | None = None
    hf_token: str | None = Field(
        default=None,
        description="HuggingFace token for pyannote diarization models.",
    )

    # Tone analysis
    enable_tone_analysis: bool = True
    tone_window_seconds: float = Field(
        default=5.0,
        description="Sliding window length for tone / energy analysis.",
    )

    # Slide alignment
    enable_slide_alignment: bool = True
