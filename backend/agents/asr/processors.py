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

try:  # pragma: no cover - groq must be installed
    from backend.core.groq_client import groq_client
except Exception:  # pragma: no cover
    groq_client = None  # type: ignore[assignment]

try:  # pragma: no cover - optional runtime dependency
    # pyrefly: ignore [missing-import]
    import librosa
except Exception:  # pragma: no cover - optional runtime dependency
    librosa = None  # type: ignore[assignment]

try:  # pragma: no cover - optional runtime dependency
    # pyrefly: ignore [missing-import]
    import soundfile as sf
except Exception:  # pragma: no cover - optional runtime dependency
    sf = None  # type: ignore[assignment]


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

async def transcribe_audio(
    audio_path: str,
    model: Any,
    language: Optional[str] = None,
    batch_size: int = 16,
) -> List[TranscriptSegment]:
    """
    Run Whisper inference on an audio file using Groq Whisper API.

    Args:
        audio_path: Path to the audio file.
        model: Groq (or AsyncGroq) client instance.
        language: Optional language code.
        batch_size: Inference batch size (ignored/kept for compatibility).

    Returns:
        List of TranscriptSegment instances.
    """
    import os
    # pyrefly: ignore [missing-import]
    from groq import AsyncGroq, Groq
    
    logger.info("Transcribing audio file via Groq: %s", audio_path)
    segments_out = []

    if not model:
        logger.warning("No ASR model/client provided.")
        return []

    # Check for fake/mock model in tests (e.g. if it has a custom __call__ or transcribe method)
    if not isinstance(model, (Groq, AsyncGroq)):
        if hasattr(model, "transcribe"):
            try:
                segments, _ = model.transcribe(str(audio_path))
                for segment in segments:
                    segments_out.append(
                        TranscriptSegment(
                            text=getattr(segment, "text", "").strip(),
                            start=float(getattr(segment, "start", 0.0)),
                            end=float(getattr(segment, "end", 0.0)),
                            confidence=float(getattr(segment, "avg_logprob", 0.0) or 0.0)
                        )
                    )
                return segments_out
            except Exception as e:
                logger.error("Failed to call mock transcribe method: %s", e)
        elif callable(model):
            try:
                result = model(audio_path)
                if isinstance(result, dict):
                    chunks = result.get("chunks") or []
                    for chunk in chunks:
                        timestamp = chunk.get("timestamp") or (0.0, 0.0)
                        segments_out.append(
                            TranscriptSegment(
                                text=chunk.get("text", "").strip(),
                                start=float(timestamp[0]),
                                end=float(timestamp[1]),
                                confidence=0.0
                            )
                        )
                    return segments_out
            except Exception as e:
                logger.error("Failed to call mock callable: %s", e)

    # Real Groq API path
    if not isinstance(audio_path, str) or not os.path.exists(audio_path):
        logger.error("Audio path %s does not exist or is not a string.", audio_path)
        return []

    filename = os.path.basename(audio_path)
    transcribe_lang = language or "en"
    
    # Check file size (Groq limit is 25 MB)
    file_size = os.path.getsize(audio_path)
    groq_limit = 25 * 1024 * 1024
    if file_size > groq_limit:
        logger.info("[Groq] Audio file size %d bytes exceeds 25MB limit. Splitting into chunks...", file_size)
        try:
            # pyrefly: ignore [missing-import]
            import soundfile as sf
            info = sf.info(audio_path)
            samplerate = info.samplerate
            total_frames = info.frames
            duration = total_frames / samplerate
            
            chunk_length_sec = 300  # 5 minutes
            overlap_sec = 5
            
            chunk_idx = 0
            all_segments = []
            
            import tempfile
            temp_dir = tempfile.gettempdir()
            
            while True:
                start_sec = chunk_idx * (chunk_length_sec - overlap_sec)
                if start_sec >= duration:
                    break
                    
                end_sec = min(start_sec + chunk_length_sec, duration)
                start_frame = int(start_sec * samplerate)
                frames_to_read = int((end_sec - start_sec) * samplerate)
                
                # Create a temp WAV file for the chunk
                chunk_file = os.path.join(temp_dir, f"audio_chunk_{chunk_idx}.wav")
                
                # Read frames and write to chunk file
                data, _ = sf.read(audio_path, start=start_frame, frames=frames_to_read, dtype='float32')
                sf.write(chunk_file, data, samplerate, subtype='PCM_16')
                
                logger.info("[Groq] transcribing chunk %d (range: %.1f - %.1f sec)", chunk_idx, start_sec, end_sec)
                
                with open(chunk_file, "rb") as f:
                    transcription = await groq_client.transcription(
                        file=f,
                        model="whisper-large-v3",
                        response_format="verbose_json",
                        language=transcribe_lang,
                        temperature=0.0
                    )
                    
                # Clean up chunk file
                try:
                    os.remove(chunk_file)
                except Exception:
                    pass
                
                # Parse segments and offset timestamps
                chunk_segments = []
                if hasattr(transcription, "segments"):
                    for segment in transcription.segments:
                        text = (segment.get("text") if isinstance(segment, dict) else getattr(segment, "text", "")).strip()
                        if text:
                            seg_start = float(segment.get("start", 0.0) if isinstance(segment, dict) else getattr(segment, "start", 0.0)) + start_sec
                            seg_end = float(segment.get("end", 0.0) if isinstance(segment, dict) else getattr(segment, "end", 0.0)) + start_sec
                            conf = float(segment.get("avg_logprob", 0.0) if isinstance(segment, dict) else getattr(segment, "avg_logprob", 0.0) or 0.0)
                            
                            chunk_segments.append(
                                TranscriptSegment(
                                    text=text,
                                    start=seg_start,
                                    end=seg_end,
                                    confidence=conf
                                )
                            )
                
                all_segments.append(chunk_segments)
                chunk_idx += 1
                
                if end_sec >= duration:
                    break
            
            # Merge transcripts from chunks
            merged_segments = []
            for c_idx, chunk_segs in enumerate(all_segments):
                for seg in chunk_segs:
                    if merged_segments:
                        last_seg = merged_segments[-1]
                        if seg.start < last_seg.end - 1.0:
                            continue
                    merged_segments.append(seg)
                    
            return merged_segments
            
        except Exception as exc:
            logger.exception("Failed splitting and transcribing audio: %s", exc)
            # Do NOT fall back to whole-file upload — it would exceed Groq's 25 MB limit.
            return []

    # Direct transcription for files within the 25 MB limit
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = await groq_client.transcription(
                file=audio_file,
                model="whisper-large-v3",
                response_format="verbose_json",
                language=transcribe_lang,
                temperature=0.0
            )
        
        # Parse segments from response
        if hasattr(transcription, "segments"):
            for segment in transcription.segments:
                text = (segment.get("text") if isinstance(segment, dict) else getattr(segment, "text", "")).strip()
                if text:
                    segments_out.append(
                        TranscriptSegment(
                            text=text,
                            start=float(segment.get("start", 0.0) if isinstance(segment, dict) else getattr(segment, "start", 0.0)),
                            end=float(segment.get("end", 0.0) if isinstance(segment, dict) else getattr(segment, "end", 0.0)),
                            confidence=float(segment.get("avg_logprob", 0.0) if isinstance(segment, dict) else getattr(segment, "avg_logprob", 0.0) or 0.0),
                        )
                    )
        elif hasattr(transcription, "text"):
            text = transcription.text.strip()
            if text:
                segments_out.append(TranscriptSegment(text=text, start=0.0, end=0.0, confidence=0.0))
    except Exception as exc:
        logger.exception("Failed to transcribe via Groq Whisper API: %s", exc)

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
        # pyrefly: ignore [missing-import]
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
        import numpy as np

        if librosa is None:
            raise ImportError("librosa is not installed")
        
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
