"""
app/agents/nodes/transcription.py
───────────────────────────────────
Node 2: Transcription
Calls OpenAI Whisper API to convert audio to text.
Long audio (> AUDIO_CHUNK_MINUTES) is split into chunks and processed in parallel.
Compatible with openai >= 2.0.
"""

import asyncio
import os
import math
import structlog
from openai import AsyncOpenAI

from app.agents.state import GraphState, TranscriptChunk
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Lazy client — initialized on first call, not at import time
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client

CHUNK_SECONDS = settings.audio_chunk_minutes * 60  # e.g. 600s = 10 min


async def _transcribe_file(file_path: str, language: str | None = None) -> dict:
    """
    Call Whisper API on a single audio file.
    Returns {text, segments: [{text, start, end}]}.
    Compatible with openai >= 2.0 where response is a Transcription object.
    """
    lang = None if language == "auto" else language
    with open(file_path, "rb") as f:
        response = await _get_client().audio.transcriptions.create(
            model=settings.whisper_model,
            file=f,
            language=lang,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    # openai 2.x: response is a Transcription object with .text and .segments
    segments = []
    raw_segments = getattr(response, "segments", None) or []
    for seg in raw_segments:
        segments.append({
            "text": getattr(seg, "text", ""),
            "start": float(getattr(seg, "start", 0)),
            "end": float(getattr(seg, "end", 0)),
        })
    return {
        "text": getattr(response, "text", ""),
        "segments": segments,
    }


def _split_audio(audio_path: str, chunk_seconds: int) -> list[tuple[str, float]]:
    """
    Split a long audio file into chunks using pydub.
    Returns list of (chunk_file_path, start_offset_seconds).
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        logger.warning("pydub not installed — skipping chunking, sending full file")
        return [(audio_path, 0.0)]

    audio = AudioSegment.from_file(audio_path)
    duration_ms = len(audio)
    chunk_ms = chunk_seconds * 1000

    chunks = []
    base, ext = os.path.splitext(audio_path)

    for i, start_ms in enumerate(range(0, duration_ms, chunk_ms)):
        end_ms = min(start_ms + chunk_ms, duration_ms)
        chunk = audio[start_ms:end_ms]
        chunk_path = f"{base}_chunk{i:03d}{ext}"
        chunk.export(chunk_path, format=ext.lstrip(".") or "mp3")
        chunks.append((chunk_path, start_ms / 1000.0))

    return chunks


async def transcription_node(state: GraphState) -> dict:
    """
    LangGraph node: transcribe audio → populate transcript and chunks.
    """
    log = logger.bind(session_id=state["session_id"], node="transcription")
    log.info("Starting transcription")

    audio_path = state["audio_path"]
    language = state.get("language", "auto")

    try:
        # ── Detect duration via file size heuristic ───────────────────────────
        # (mutagen is optional; we rely on config's chunk minutes)
        try:
            from mutagen import File as MutagenFile
            mf = MutagenFile(audio_path)
            duration_sec = mf.info.length if mf and mf.info else None
        except Exception:
            duration_sec = None

        needs_chunking = (
            duration_sec is not None and duration_sec > CHUNK_SECONDS
        ) or (
            # Fallback: chunk if file > 25MB (rough proxy for ~10 min audio)
            os.path.getsize(audio_path) > 25 * 1024 * 1024
        )

        if needs_chunking:
            log.info("Long audio detected — splitting into chunks", duration_sec=duration_sec)
            chunk_pairs = _split_audio(audio_path, CHUNK_SECONDS)

            # Transcribe all chunks in parallel
            tasks = [_transcribe_file(path, language) for path, _ in chunk_pairs]
            results = await asyncio.gather(*tasks)

            # Stitch transcript and offset timestamps
            full_text_parts = []
            all_chunks: list[TranscriptChunk] = []

            for (chunk_path, offset), result in zip(chunk_pairs, results):
                full_text_parts.append(result["text"])
                for seg in result["segments"]:
                    all_chunks.append(
                        TranscriptChunk(
                            text=seg["text"],
                            start=seg["start"] + offset,
                            end=seg["end"] + offset,
                        )
                    )
                # Clean up temp chunk files
                if chunk_path != audio_path:
                    try:
                        os.remove(chunk_path)
                    except OSError:
                        pass

            transcript = " ".join(full_text_parts).strip()
        else:
            log.info("Short audio — transcribing directly")
            result = await _transcribe_file(audio_path, language)
            transcript = result["text"].strip()
            all_chunks: list[TranscriptChunk] = [
                TranscriptChunk(text=s["text"], start=s["start"], end=s["end"])
                for s in result["segments"]
            ]

        word_count = len(transcript.split())
        log.info("Transcription complete", words=word_count, chunks=len(all_chunks))

        return {
            "transcript": transcript,
            "chunks": all_chunks,
            "current_step": "guardrail_pre",
            "error": None,
        }

    except Exception as exc:
        log.error("Transcription failed", error=str(exc))
        return {
            "transcript": "",
            "chunks": [],
            "current_step": "guardrail_pre",
            "error": f"Transcription failed: {exc}",
        }
