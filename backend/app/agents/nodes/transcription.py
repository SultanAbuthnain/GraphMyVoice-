"""
app/agents/nodes/transcription.py
───────────────────────────────────
Node 2: Transcription
Calls Google Gemini to natively transcribe audio to text and extract segment timestamps.
Replaces the old Whisper + pydub chunking logic with a single prompt to gemini-1.5-flash
which handles large audio files flawlessly.
"""

import os
import json
import asyncio
import structlog
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.agents.state import GraphState, TranscriptChunk
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

class Segment(BaseModel):
    text: str
    start: float
    end: float

class TranscriptionResponse(BaseModel):
    text: str
    segments: list[Segment]

async def _transcribe_file(audio_path: str, language: str | None = None) -> TranscriptionResponse:
    """
    Uploads audio to Gemini and prompts it to extract the transcription and segments.
    """
    client = _get_client()
    
    # 1. Upload the file to Gemini File API
    # google-genai is synchronous for file uploads, we could run in executor if needed
    uploaded_file = await asyncio.to_thread(client.files.upload, file=audio_path)
    
    try:
        lang_prompt = f" The audio language is {language}." if language and language != "auto" else ""
        prompt = (
            f"Transcribe the attached audio.{lang_prompt} "
            "Return a JSON object containing the full transcript in 'text' and an array of 'segments'. "
            "Each segment must contain 'text' (the spoken words), 'start' (start timestamp in seconds), "
            "and 'end' (end timestamp in seconds)."
        )

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-1.5-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TranscriptionResponse,
                temperature=0.1
            )
        )
        
        # Parse the structured response
        if response.text:
            return TranscriptionResponse.model_validate_json(response.text)
        else:
            raise ValueError("Empty response from Gemini")
            
    finally:
        # 3. Always clean up the uploaded file to avoid storage bloat
        await asyncio.to_thread(client.files.delete, name=uploaded_file.name)


async def transcription_node(state: GraphState) -> dict:
    """
    LangGraph node: transcribe audio → populate transcript and chunks.
    """
    log = logger.bind(session_id=state["session_id"], node="transcription")
    log.info("Starting transcription via Gemini")

    audio_path = state["audio_path"]
    language = state.get("language", "auto")

    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        result = await _transcribe_file(audio_path, language)

        transcript = result.text.strip()
        all_chunks: list[TranscriptChunk] = [
            TranscriptChunk(text=s.text, start=s.start, end=s.end)
            for s in result.segments
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
