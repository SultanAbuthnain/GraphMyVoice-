"""
app/agents/nodes/persistence.py
─────────────────────────────────
Node 7: Persistence
Writes the final mindmap to the database:
  1. Upserts all MindmapNode and MindmapEdge rows
  2. Creates Task rows (is_done=False) for every task node
  3. Updates the Session status to 'completed'
"""

import uuid
import bleach
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import GraphState
from app.database import AsyncSessionLocal
from app.models.mindmap_node import MindmapNode
from app.models.mindmap_edge import MindmapEdge
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

    session_id = uuid.UUID(state["session_id"])
    nodes = state.get("mindmap_nodes", [])
    edges = state.get("mindmap_edges", [])
    validation_score = state.get("validation_score", 0.0)
    transcript = state.get("transcript", "")

    try:
        async with AsyncSessionLocal() as db:
            # ── 1. Delete old nodes and edges (in case of regeneration) ─────────────────
            # SQLAlchemy CASCADE will handle edges and tasks when nodes are deleted
            old_nodes = await db.execute(
                select(MindmapNode).where(MindmapNode.session_id == session_id)
            )
            for old_node in old_nodes.scalars():
                await db.delete(old_node)
            
            # ── 2. Insert new nodes ────────────────────────────────────────────
            for node_data in nodes:
                db_node = MindmapNode(
                    id=uuid.UUID(node_data["id"]),
                    session_id=session_id,
                    parent_id=uuid.UUID(node_data["parent_id"]) if node_data.get("parent_id") else None,
                    type=node_data["type"],
                    label=_sanitize(node_data["label"]),
                    description=_sanitize(node_data["description"]) if node_data.get("description") else None,
                    position_x=node_data.get("position_x", 0.0),
                    position_y=node_data.get("position_y", 0.0),
                    order_index=node_data.get("order_index", 0),
                )
                db.add(db_node)

                # ── 3. Create Task row for task-type nodes ────────────────────
                if node_data["type"] == "task":
                    db_task = Task(
                        session_id=session_id,
                        node_id=uuid.UUID(node_data["id"]),
                        title=_sanitize(node_data["label"]),
                        is_done=False,
                    )
                    db.add(db_task)
            
            # ── 4. Insert new edges ────────────────────────────────────────────
            for edge_data in edges:
                db_edge = MindmapEdge(
                    id=uuid.UUID(edge_data["id"]),
                    session_id=session_id,
                    source_node_id=uuid.UUID(edge_data["source_node_id"]),
                    target_node_id=uuid.UUID(edge_data["target_node_id"]),
                    relationship_type=_sanitize(edge_data["relationship_type"]),
                )
                db.add(db_edge)

            # ── 5. Update session status ──────────────────────────────────────
            await db.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(
                    status="completed",
                    transcript=transcript,
                )
            )

            await db.commit()

        log.info(
            "Persistence complete",
            nodes_saved=len(nodes),
            edges_saved=len(edges),
            validation_score=f"{validation_score:.2f}",
        )
        return {
            "current_step": "completed",
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
                        error_message=f"Persistence failed: {str(exc)}",
                    )
                )
                await db.commit()
        except Exception:
            pass
        return {"current_step": "failed", "error": f"Persistence failed: {exc}"}
