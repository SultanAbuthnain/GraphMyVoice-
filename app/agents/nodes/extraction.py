"""
app/agents/nodes/extraction.py
────────────────────────────────
Node 4: Extraction Agent
Sends the transcript to Claude and extracts a structured goals/plans/tasks JSON.
Uses Pydantic structured output via langchain-anthropic to enforce the schema.
Retries up to settings.llm_max_retries times on failure.
"""

import json
import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
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


# ── LLM client with structured output ────────────────────────────────────────

def _get_llm():
    return ChatAnthropic(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.anthropic_api_key,
    ).with_structured_output(ExtractedContent)


async def extraction_node(state: GraphState) -> dict:
    """
    LangGraph node: extract goals/plans/tasks from transcript using Claude.
    Increments retry_count on each call; state controls retry loop via graph routing.
    """
    log = logger.bind(session_id=state["session_id"], node="extraction")
    retry = state.get("retry_count", 0)
    log.info("Running extraction", attempt=retry + 1)

    transcript = state.get("transcript", "")

    try:
        llm = _get_llm()
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=EXTRACTION_USER_TEMPLATE.format(transcript=transcript)
            ),
        ]

        result: ExtractedContent = await llm.ainvoke(messages)

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
