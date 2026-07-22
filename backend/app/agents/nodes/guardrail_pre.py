"""
app/agents/nodes/guardrail_pre.py
───────────────────────────────────
Node 3: Pre-processing Guardrail
Checks the transcript quality BEFORE sending it to the LLM.
Fails fast if the transcript is empty, too short, or too garbled.
"""

import re
import structlog

from app.agents.state import GraphState
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Whisper noise markers that indicate bad audio quality
WHISPER_NOISE_PATTERNS = [
    r"\[BLANK_AUDIO\]",
    r"\[inaudible\]",
    r"\[music\]",
    r"\[applause\]",
    r"\.\.\.",           # many consecutive ellipses
]


def _count_noise_markers(text: str) -> int:
    count = 0
    for pattern in WHISPER_NOISE_PATTERNS:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


async def guardrail_pre_node(state: GraphState) -> dict:
    """
    LangGraph node: validate transcript quality.
    Sets state['error'] to fail the pipeline, or clears it to proceed.
    """
    log = logger.bind(session_id=state["session_id"], node="guardrail_pre")
    log.info("Running pre-extraction guardrail")

    transcript = state.get("transcript", "")
    flags: list[str] = []

    # ── Check 1: Transcript not empty ────────────────────────────────────────
    if not transcript.strip():
        error = "Transcript is empty. The audio may be silent or inaudible."
        log.warning(error)
        return {"error": error, "validation_flags": [error], "current_step": "guardrail_pre"}

    # ── Check 2: Minimum word count ───────────────────────────────────────────
    word_count = len(transcript.split())
    if word_count < settings.min_transcript_words:
        error = (
            f"Transcript too short ({word_count} words). "
            f"Minimum required: {settings.min_transcript_words} words."
        )
        log.warning(error)
        return {"error": error, "validation_flags": [error], "current_step": "guardrail_pre"}

    # ── Check 3: Noise marker ratio ───────────────────────────────────────────
    noise_count = _count_noise_markers(transcript)
    noise_ratio = noise_count / max(word_count, 1)
    if noise_ratio > 0.20:
        flag = f"High noise ratio in transcript ({noise_ratio:.1%}). Audio quality may be poor."
        flags.append(flag)
        log.warning(flag)
        # This is a WARNING, not a hard failure — pipeline continues with a flag

    # ── Check 4: Truncate if too long for LLM context ─────────────────────────
    # Claude 3.5 Sonnet has 200k token context, but we keep it practical
    MAX_CHARS = 150_000  # ~37k tokens
    if len(transcript) > MAX_CHARS:
        transcript = transcript[:MAX_CHARS]
        flag = f"Transcript truncated to {MAX_CHARS} chars to fit LLM context window."
        flags.append(flag)
        log.info(flag)

    log.info("Pre-guardrail passed", words=word_count, noise_ratio=f"{noise_ratio:.1%}", flags=len(flags))
    return {
        "transcript": transcript,
        "validation_flags": flags,
        "current_step": "extracting",
        "error": None,
    }
