"""
app/agents/nodes/extraction.py
────────────────────────────────
Node 4: Extraction Agent
Sends the transcript to Groq (Llama) and extracts a structured goals/plans/tasks JSON.
Uses Groq's free-tier LLM with structured JSON output to enforce the schema.
Retries up to settings.llm_max_retries times on failure.
"""

import json
import asyncio
import structlog
from groq import Groq
from pydantic import BaseModel, Field

from app.agents.state import GraphState
from app.agents.prompts.extraction_prompt import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_TEMPLATE,
)
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


# ── Pydantic schema for structured output ─────────────────────────────────────

class Task(BaseModel):
    id: str
    title: str
    owner: str | None = None
    due: str | None = None


class Plan(BaseModel):
    id: str
    title: str
    tasks: list[Task] = Field(default_factory=list)


class Goal(BaseModel):
    id: str
    title: str
    plans: list[Plan] = Field(default_factory=list)


class ExtractedContent(BaseModel):
    topic: str
    goals: list[Goal] = Field(default_factory=list)


# ── Groq client ───────────────────────────────────────────────────────────────

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


async def _extract_with_groq(transcript: str) -> ExtractedContent:
    client = _get_client()

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": EXTRACTION_USER_TEMPLATE.format(transcript=transcript)},
    ]

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=settings.llm_model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=settings.llm_temperature,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return ExtractedContent.model_validate(data)


async def extraction_node(state: GraphState) -> dict:
    """
    LangGraph node: extract goals/plans/tasks from transcript using Groq.
    Increments retry_count on each call; state controls retry loop via graph routing.
    """
    log = logger.bind(session_id=state["session_id"], node="extraction")
    retry = state.get("retry_count", 0)
    log.info("Running extraction", attempt=retry + 1)

    transcript = state.get("transcript", "")

    try:
        result = await _extract_with_groq(transcript)

        extracted = result.model_dump()
        log.info(
            "Extraction successful",
            goals=len(extracted["goals"]),
            attempt=retry + 1,
        )

        return {
            "extracted_json": extracted,
            "retry_count": retry + 1,
            "current_step": "building_mindmap",
            "error": None,
        }

    except Exception as exc:
        log.error("Extraction failed", error=str(exc), attempt=retry + 1)
        return {
            "extracted_json": {},
            "retry_count": retry + 1,
            "current_step": "extraction",
            "error": f"Extraction attempt {retry + 1} failed: {exc}",
        }
