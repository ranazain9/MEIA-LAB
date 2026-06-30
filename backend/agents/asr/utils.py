"""
ASR Utilities
=============

Helper functions for audio preprocessing, format conversion,
and feature extraction.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def validate_audio_file(path: str) -> Path:
    """Validate that the audio file exists and has a supported extension."""
    audio_path = Path(path)
    supported = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if audio_path.suffix.lower() not in supported:
        raise ValueError(
            f"Unsupported audio format '{audio_path.suffix}'. "
            f"Supported: {supported}"
        )
    return audio_path


def seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def compute_speaking_pace(
    word_count: int, duration_seconds: float
) -> float:
    """Return words per minute."""
    if duration_seconds <= 0:
        return 0.0
    return (word_count / duration_seconds) * 60.0
