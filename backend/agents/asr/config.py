"""
ASR Agent Configuration
=======================

All configurable knobs for the ASR & Alignment Agent.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class ASRConfig(BaseModel):
    """Configuration for the ASR & Alignment Agent."""

    # Model settings
    whisper_model: str = Field(
        default="whisper-large-v3",
        description="Whisper model variant to load. Defaults to Groq's whisper-large-v3.",
    )
    device: str = Field(
        default="cpu",
        description="Compute device (cuda / cpu) - Deprecated for Groq API.",
    )
    compute_type: str = Field(
        default="float32",
        description="Precision for inference - Deprecated for Groq API.",
    )
    groq_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GROQ_API_KEY"),
        description="API Key for Groq Whisper transcription API."
    )


    # Transcription
    language: str | None = Field(
        default=None,
        description="Force a specific language code (e.g. 'en'). None = auto-detect.",
    )
    batch_size: int = Field(default=16, ge=1)

    # Diarization
    enable_diarization: bool = False
    min_speakers: int | None = None
    max_speakers: int | None = None
    hf_token: str | None = Field(
        default=None,
        description="HuggingFace token for pyannote diarization models. Reads from the environment if not provided.",
    )

    # Tone analysis
    enable_tone_analysis: bool = True
    tone_window_seconds: float = Field(
        default=5.0,
        description="Sliding window length for tone / energy analysis.",
    )

    # Slide alignment
    enable_slide_alignment: bool = True
