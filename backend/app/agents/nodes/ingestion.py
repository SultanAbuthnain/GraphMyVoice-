"""
app/agents/nodes/ingestion.py
──────────────────────────────
Node 1: Ingestion
Validates the audio file (type, size, duration) and updates the session status.
"""

import os
import structlog

from app.agents.state import GraphState
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Audio duration detection — try mutagen first, fallback to a file-size estimate
try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


def _get_duration_seconds(audio_path: str) -> float | None:
    """Return audio duration in seconds, or None if detection fails."""
    if HAS_MUTAGEN:
        try:
            audio = MutagenFile(audio_path)
            if audio and audio.info:
                return audio.info.length
        except Exception:
            pass
    return None


async def ingestion_node(state: GraphState) -> dict:
    """
    LangGraph node: validate the uploaded audio file.
    Returns a partial state update dict.
    """
    log = logger.bind(session_id=state["session_id"], node="ingestion")
    log.info("Starting ingestion")

    audio_path = state["audio_path"]

    # ── 1. File existence check ───────────────────────────────────────────────
    if not os.path.exists(audio_path):
        log.error("Audio file not found", path=audio_path)
        return {
            "current_step": "ingestion",
            "error": f"Audio file not found: {audio_path}",
        }

    # ── 2. File size check ────────────────────────────────────────────────────
    size_bytes = os.path.getsize(audio_path)
    if size_bytes > settings.max_file_size_bytes:
        log.error("File too large", size_mb=size_bytes / 1024 / 1024)
        return {
            "current_step": "ingestion",
            "error": f"File size {size_bytes / 1024 / 1024:.1f}MB exceeds limit of {settings.max_file_size_mb}MB",
        }

    # ── 3. Duration check ─────────────────────────────────────────────────────
    duration = _get_duration_seconds(audio_path)
    if duration is not None:
        max_duration = settings.max_audio_duration_minutes * 60
        if duration > max_duration:
            log.error("Audio too long", duration_min=duration / 60)
            return {
                "current_step": "ingestion",
                "error": f"Audio duration {duration / 60:.1f} min exceeds max of {settings.max_audio_duration_minutes} min",
            }
        log.info("Audio duration OK", duration_seconds=duration)

    log.info("Ingestion passed", size_bytes=size_bytes)
    return {
        "current_step": "transcribing",
        "error": None,
    }
