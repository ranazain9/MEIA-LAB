"""
ASR & Alignment Agent
=====================

Speech recognition, speaker diarization, tone analysis,
and slide-transcript temporal alignment.

Models:
    - Whisper Large V3 (transcription)
    - WhisperX (alignment & diarization)
"""

from backend.agents.asr.agent import ASRAgent
from backend.agents.asr.config import ASRConfig

__all__ = ["ASRAgent", "ASRConfig"]
