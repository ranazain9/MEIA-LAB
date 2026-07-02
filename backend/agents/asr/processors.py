"""
ASR Processors
==============

Isolated processing functions for transcription, alignment,
diarization, and tone analysis. Kept separate from the agent
class for testability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------

@dataclass
class TranscriptSegment:
    """A single transcribed segment."""

    text: str
    start: float
    end: float
    speaker: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ToneWindow:
    """Tone analysis for a sliding window of audio."""

    start: float
    end: float
    energy: float = 0.0
    pace_wpm: float = 0.0
    hesitation_count: int = 0
    sentiment_label: str = "neutral"
    sentiment_score: float = 0.0


@dataclass
class SlideAlignment:
    """Maps a slide to its corresponding transcript range."""

    slide_index: int
    slide_start: float
    slide_end: float
    segments: List[TranscriptSegment] = field(default_factory=list)


# ------------------------------------------------------------------
# Processors
# ------------------------------------------------------------------

def normalize_whisper_model_name(model_name: Optional[str]) -> str:
    """Translate shorthand Whisper names to Hugging Face model IDs."""
    if not model_name:
        return "openai/whisper-large-v3"
    if model_name.startswith("openai/"):
        return model_name
    if model_name in {"tiny", "base", "small", "medium", "large", "large-v2", "large-v3"}:
        return f"openai/whisper-{model_name}"
    if model_name.startswith("whisper-"):
        return f"openai/{model_name}"
    return model_name


def build_transformers_pipeline(
    model_name: Optional[str],
    device: str = "cpu",
    compute_type: str = "float32",
    batch_size: int = 16,
) -> Any:
    """Create a Hugging Face ASR pipeline with safe CPU/GPU fallback behavior."""
    try:
        from transformers import pipeline
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("Transformers ASR pipeline unavailable: %s", exc)
        return None

    normalized_name = normalize_whisper_model_name(model_name)
    try:
        device_str = str(device).lower()
        use_cuda = device_str.startswith("cuda") and torch.cuda.is_available()
        if device_str.startswith("cuda") and not torch.cuda.is_available():
            logger.warning("CUDA requested but unavailable; falling back to CPU.")

        torch_device = 0 if use_cuda else -1
        pipeline_kwargs: Dict[str, Any] = {
            "task": "automatic-speech-recognition",
            "model": normalized_name,
            "device": torch_device,
            "batch_size": batch_size,
        }

        if use_cuda:
            if str(compute_type).lower() == "float16":
                pipeline_kwargs["torch_dtype"] = torch.float16
            elif str(compute_type).lower() == "float32":
                pipeline_kwargs["torch_dtype"] = torch.float32
        return pipeline(**pipeline_kwargs)
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("Failed to initialize Transformers ASR pipeline: %s", exc)
        return None


async def transcribe_audio(
    audio_path: str,
    model: Any,
    language: Optional[str] = None,
    batch_size: int = 16,
) -> List[TranscriptSegment]:
    """
    Run Whisper inference on an audio file.

    Args:
        audio_path: Path to the audio file.
        model: Loaded Whisper model instance.
        language: Optional language code.
        batch_size: Inference batch size.

    Returns:
        List of TranscriptSegment instances.
    """
    logger.info("Transcribing: %s", audio_path)
    segments_out = []

    if not model:
        logger.warning("No ASR model provided.")
        return []

    try:
        if hasattr(model, "transcribe"):
            segments, _ = model.transcribe(audio_path, beam_size=5)
            for segment in segments:
                segments_out.append(
                    TranscriptSegment(
                        text=segment.text.strip(),
                        start=segment.start,
                        end=segment.end,
                        confidence=getattr(segment, "no_speech_prob", 0.0),
                    )
                )
            return segments_out

        result = model(
            audio_path,
            return_timestamps=True,
            chunk_length_s=30,
            generate_kwargs={"language": language} if language else {},
        )
        if isinstance(result, dict):
            chunks = result.get("chunks") or []
            if chunks:
                for chunk in chunks:
                    timestamp = chunk.get("timestamp") if isinstance(chunk, dict) else None
                    if isinstance(timestamp, (list, tuple)) and len(timestamp) == 2:
                        start, end = timestamp
                    else:
                        start, end = 0.0, 0.0
                    text = (chunk.get("text") or "").strip() if isinstance(chunk, dict) else ""
                    if text:
                        segments_out.append(
                            TranscriptSegment(text=text, start=float(start), end=float(end), confidence=0.0)
                        )
            else:
                text = (result.get("text") or "").strip()
                if text:
                    segments_out.append(TranscriptSegment(text=text, start=0.0, end=0.0, confidence=0.0))
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    text = (item.get("text") or "").strip()
                    if text:
                        segments_out.append(TranscriptSegment(text=text, start=0.0, end=0.0, confidence=0.0))
    except Exception as exc:
        logger.error("Failed to transcribe audio: %s", exc)

    return segments_out


async def align_transcript(
    segments: List[TranscriptSegment],
    audio_path: str,
    align_model: Any,
) -> List[TranscriptSegment]:
    """Refine word-level timestamps using WhisperX forced alignment."""
    # TODO: Implement alignment
    return segments


async def diarize_speakers(
    segments: List[TranscriptSegment],
    audio_path: str,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
) -> List[TranscriptSegment]:
    """Assign speaker labels to transcript segments using pyannote."""
    if not segments:
        return segments
        
    try:
        import os
        from pyannote.audio import Pipeline
        hf_token = os.environ.get("HF_TOKEN")
        
        if not hf_token:
            logger.warning("HF_TOKEN not found, skipping diarization.")
            return segments
            
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
        if pipeline:
            diarization = pipeline(audio_path, min_speakers=min_speakers, max_speakers=max_speakers)
            
            # Simple heuristic mapping
            for segment in segments:
                # find the speaker with the most overlap
                best_speaker = None
                best_overlap = 0
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    overlap = max(0, min(segment.end, turn.end) - max(segment.start, turn.start))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_speaker = speaker
                if best_speaker:
                    segment.speaker = best_speaker
                    
    except Exception as exc:
        logger.error("Diarization failed: %s", exc)
        
    return segments


async def analyze_tone(
    audio_path: str,
    segments: List[TranscriptSegment],
    window_seconds: float = 5.0,
) -> List[ToneWindow]:
    """Compute per-window tone, pace, and hesitation metrics."""
    windows = []
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        for start_t in np.arange(0, duration, window_seconds):
            end_t = min(start_t + window_seconds, duration)
            start_sample = int(start_t * sr)
            end_sample = int(end_t * sr)
            y_window = y[start_sample:end_sample]
            
            energy = float(np.sum(y_window**2) / len(y_window)) if len(y_window) > 0 else 0.0
            
            windows.append(
                ToneWindow(
                    start=start_t,
                    end=end_t,
                    energy=energy,
                )
            )
    except Exception as exc:
        logger.error("Tone analysis failed: %s", exc)
        
    return windows


async def align_slides_to_transcript(
    segments: List[TranscriptSegment],
    slide_timestamps: List[float],
) -> List[SlideAlignment]:
    """Map slide boundaries to transcript segments."""
    alignments = []
    if not slide_timestamps:
        return alignments
        
    # Simply chunk the segments into the slide windows
    timestamps = slide_timestamps + [float('inf')]
    
    for i in range(len(slide_timestamps)):
        start_t = timestamps[i]
        end_t = timestamps[i+1]
        
        slide_segments = [s for s in segments if s.start >= start_t and s.start < end_t]
        
        alignments.append(
            SlideAlignment(
                slide_index=i,
                slide_start=start_t,
                slide_end=end_t if end_t != float('inf') else slide_segments[-1].end if slide_segments else start_t,
                segments=slide_segments
            )
        )
        
    return alignments
