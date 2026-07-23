"""
app/agents/nodes/transcription.py
───────────────────────────────────
Node 2: Transcription
Sends the uploaded audio file to Groq's Whisper API (free tier) to
transcribe it. Returns a full transcript string and a list of timed
chunks used by downstream nodes.
"""

import os
import asyncio
import structlog
from groq import Groq

from app.agents.state import GraphState, TranscriptChunk
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


async def _transcribe_file(audio_path: str, language: str | None = None) -> dict:
    """
    Uploads audio to Groq Whisper and returns transcription with word-level timestamps.
    """
    client = _get_client()

    lang = None if (not language or language == "auto") else language

    with open(audio_path, "rb") as f:
        response = await asyncio.to_thread(
            client.audio.transcriptions.create,
            file=(os.path.basename(audio_path), f),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language=lang,
        )

    return response


async def transcription_node(state: GraphState) -> dict:
    """
    LangGraph node: transcribe audio → populate transcript and chunks.
    """
    log = logger.bind(session_id=state["session_id"], node="transcription")
    log.info("Starting transcription via Groq Whisper")

    audio_path = state["audio_path"]
    language = state.get("language", "auto")

    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        response = await _transcribe_file(audio_path, language)

        transcript = response.text.strip() if hasattr(response, "text") else ""

        # Build timed chunks from Groq's segment timestamps
        all_chunks: list[TranscriptChunk] = []
        segments = getattr(response, "segments", None) or []
        for seg in segments:
            all_chunks.append(
                TranscriptChunk(
                    text=seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", ""),
                    start=seg.get("start", 0.0) if isinstance(seg, dict) else getattr(seg, "start", 0.0),
                    end=seg.get("end", 0.0) if isinstance(seg, dict) else getattr(seg, "end", 0.0),
                )
            )

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
