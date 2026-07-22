"""
app/agents/graph.py
────────────────────
Assembles the LangGraph StateGraph for the full audio-to-mindmap pipeline.

Graph flow:
  ingestion → transcription → guardrail_pre
    → [FAIL] END with error
    → [PASS] extraction → mindmap_builder → guardrail_post
        → [LOW SCORE + retries left] extraction (retry)
        → [LOW SCORE + no retries]  persistence with warning
        → [HIGH SCORE]              persistence → END
"""

from langgraph.graph import END, StateGraph

from app.agents.state import GraphState
from app.agents.nodes.ingestion import ingestion_node
from app.agents.nodes.transcription import transcription_node
from app.agents.nodes.guardrail_pre import guardrail_pre_node
from app.agents.nodes.extraction import extraction_node
from app.agents.nodes.mindmap_builder import mindmap_builder_node
from app.agents.nodes.guardrail_post import guardrail_post_node
from app.agents.nodes.persistence import persistence_node
from app.config import get_settings

settings = get_settings()


# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_guardrail_pre(state: GraphState) -> str:
    """After pre-guardrail: fail fast or continue to extraction."""
    if state.get("error"):
        return "end_with_error"
    return "extraction"


def route_after_guardrail_post(state: GraphState) -> str:
    """
    After post-guardrail (hallucination check):
    - If score is high enough → persist
    - If score is low but we have retries left → retry extraction
    - If score is low and retries exhausted → persist anyway with warning flag
    """
    score = state.get("validation_score", 1.0)
    retries = state.get("retry_count", 0)
    threshold = settings.hallucination_threshold

    if score >= threshold:
        return "persistence"

    if retries < settings.llm_max_retries:
        return "extraction"  # retry

    # Max retries reached — save with warning
    return "persistence"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)

    # Register nodes
    builder.add_node("ingestion",       ingestion_node)
    builder.add_node("transcription",   transcription_node)
    builder.add_node("guardrail_pre",   guardrail_pre_node)
    builder.add_node("extraction",      extraction_node)
    builder.add_node("mindmap_builder", mindmap_builder_node)
    builder.add_node("guardrail_post",  guardrail_post_node)
    builder.add_node("persistence",     persistence_node)

    # Entry point
    builder.set_entry_point("ingestion")

    # Linear edges
    builder.add_edge("ingestion",       "transcription")
    builder.add_edge("transcription",   "guardrail_pre")

    # Conditional after pre-guardrail
    builder.add_conditional_edges(
        "guardrail_pre",
        route_after_guardrail_pre,
        {
            "extraction":    "extraction",
            "end_with_error": END,
        },
    )

    builder.add_edge("extraction",      "mindmap_builder")
    builder.add_edge("mindmap_builder", "guardrail_post")

    # Conditional after post-guardrail
    builder.add_conditional_edges(
        "guardrail_post",
        route_after_guardrail_post,
        {
            "extraction":  "extraction",   # retry loop
            "persistence": "persistence",
        },
    )

    builder.add_edge("persistence", END)

    return builder.compile()


# Compiled graph — import this in pipeline_service.py
graph = build_graph()
