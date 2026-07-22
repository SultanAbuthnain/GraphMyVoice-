"""
app/agents/nodes/guardrail_post.py
────────────────────────────────────
Node 6: Post-processing Guardrail (Hallucination Check)
For every generated task, verifies it can be traced back to at least one
keyword found in the transcript. Computes a coverage_score (0.0 - 1.0).
The graph routing in graph.py uses this score to decide retry vs. persist.
"""

import re
import structlog
from app.agents.state import GraphState
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Words to ignore when matching (stop words)
STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "should", "could", "may",
    "من", "في", "على", "إلى", "مع", "هذا", "هذه", "التي", "الذي",
    "كان", "يكون", "لا", "لم", "أن", "ما", "هو", "هي",
}


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful words from a node label, filtering stop words."""
    words = re.findall(r"\b\w{3,}\b", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def _node_covered_in_transcript(node_label: str, transcript_lower: str) -> bool:
    """
    Returns True if at least one meaningful keyword from node_label
    appears in the transcript.
    """
    keywords = _extract_keywords(node_label)
    if not keywords:
        return True  # Nothing to check — give benefit of the doubt
    return any(kw in transcript_lower for kw in keywords)


async def guardrail_post_node(state: GraphState) -> dict:
    """
    LangGraph node: hallucination check on the generated mindmap.
    Computes validation_score and appends any flags.
    """
    log = logger.bind(session_id=state["session_id"], node="guardrail_post")
    log.info("Running post-extraction guardrail")

    transcript = state.get("transcript", "").lower()
    nodes = state.get("mindmap_nodes", [])
    flags = list(state.get("validation_flags", []))

    # Only validate task nodes (leaf nodes) — goals/plans are more abstract
    task_nodes = [n for n in nodes if n["node_type"] == "task"]

    if not task_nodes:
        log.warning("No task nodes to validate — setting score to 1.0")
        return {
            "validation_score": 1.0,
            "validation_flags": flags,
            "current_step": "saving",
            "error": None,
        }

    # ── Hallucination check ───────────────────────────────────────────────────
    covered = 0
    for task_node in task_nodes:
        label = task_node["label"]
        if _node_covered_in_transcript(label, transcript):
            covered += 1
        else:
            flag = f"Possible hallucination: task '{label}' has no match in transcript"
            flags.append(flag)
            log.warning("Unverified task", label=label)

    score = covered / len(task_nodes)

    # ── JSON structure validation ─────────────────────────────────────────────
    required_fields = {"id", "parent_id", "label", "node_type", "order_index"}
    for node in nodes:
        missing = required_fields - set(node.keys())
        if missing:
            flag = f"Node '{node.get('id', '?')}' missing fields: {missing}"
            flags.append(flag)
            log.warning(flag)

    log.info(
        "Post-guardrail complete",
        score=f"{score:.2f}",
        tasks_checked=len(task_nodes),
        covered=covered,
        flags=len(flags),
    )

    return {
        "validation_score": score,
        "validation_flags": flags,
        "current_step": "saving",
        "error": None,
    }
