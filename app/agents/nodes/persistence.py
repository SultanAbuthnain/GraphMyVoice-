"""
app/agents/nodes/persistence.py
─────────────────────────────────
Node 7: Persistence
Writes the final mindmap to the database:
  1. Upserts all MindmapNode rows
  2. Creates Task rows (is_checked=False) for every task node
  3. Updates the Session status to 'done'
"""

import uuid
import bleach
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import GraphState
from app.database import AsyncSessionLocal
from app.models.mindmap_node import MindmapNode
from app.models.task import Task
from app.models.session import Session

logger = structlog.get_logger()

# Allowed HTML in node labels (none — strip everything)
ALLOWED_TAGS: list[str] = []
ALLOWED_ATTRS: dict = {}


def _sanitize(text: str) -> str:
    """Strip any HTML/JS from LLM-generated text before persisting."""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


async def persistence_node(state: GraphState) -> dict:
    """
    LangGraph node: write mindmap data to PostgreSQL.
    Uses its own session (not the HTTP request session).
    """
    log = logger.bind(session_id=state["session_id"], node="persistence")
    log.info("Persisting mindmap to database")

    session_id = state["session_id"]
    nodes = state.get("mindmap_nodes", [])
    validation_score = state.get("validation_score", 0.0)
    transcript = state.get("transcript", "")

    try:
        async with AsyncSessionLocal() as db:
            # ── 1. Delete old nodes (in case of regeneration) ─────────────────
            old_nodes = await db.execute(
                select(MindmapNode).where(MindmapNode.session_id == session_id)
            )
            for old_node in old_nodes.scalars():
                await db.delete(old_node)

            # ── 2. Insert new nodes ────────────────────────────────────────────
            for node_data in nodes:
                db_node = MindmapNode(
                    id=node_data["id"],
                    session_id=session_id,
                    parent_id=node_data.get("parent_id"),
                    label=_sanitize(node_data["label"]),
                    node_type=node_data["node_type"],
                    order_index=node_data.get("order_index", 0),
                    source_ref=node_data.get("source_ref"),
                )
                db.add(db_node)

                # ── 3. Create Task row for task-type nodes ────────────────────
                if node_data["node_type"] == "task":
                    db_task = Task(
                        node_id=node_data["id"],
                        is_checked=False,
                        due_date=None,
                        owner=None,
                    )
                    db.add(db_task)

            # ── 4. Update session status ──────────────────────────────────────
            word_count = len(transcript.split()) if transcript else 0
            await db.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(
                    status="done",
                    progress_percent=100,
                    current_step="saving",
                    transcript=transcript,
                    transcript_word_count=word_count,
                    steps_json=_build_steps_done(),
                )
            )

            await db.commit()

        log.info(
            "Persistence complete",
            nodes_saved=len(nodes),
            validation_score=f"{validation_score:.2f}",
        )
        return {
            "current_step": "done",
            "error": None,
        }

    except Exception as exc:
        log.error("Persistence failed", error=str(exc))
        # Update session status to failed
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(
                        status="failed",
                        error_json={"code": "persistence_failed", "message": str(exc), "retryable": False},
                    )
                )
                await db.commit()
        except Exception:
            pass
        return {"current_step": "done", "error": f"Persistence failed: {exc}"}


def _build_steps_done() -> list[dict]:
    """Return the completed steps list for the status endpoint."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    steps = [
        ("ingestion",       "استلام الملف"),
        ("transcribing",    "تفريغ الصوت"),
        ("extracting",      "استخراج المحتوى"),
        ("building_mindmap","بناء الخريطة الذهنية"),
        ("validating",      "التحقق من الجودة"),
        ("saving",          "حفظ النتائج"),
    ]
    return [{"name": name, "label": label, "status": "done", "completed_at": now} for name, label in steps]
