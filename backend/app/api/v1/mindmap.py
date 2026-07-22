"""
app/api/v1/mindmap.py
──────────────────────
Endpoint:
  GET /sessions/{id}/mindmap  → return full mind map JSON
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserPayload, get_current_user, get_db
from app.models.mindmap_node import MindmapNode
from app.models.mindmap_edge import MindmapEdge

router = APIRouter()


@router.get("/{session_id}/mindmap", status_code=status.HTTP_200_OK)
async def get_mindmap(
    session_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the complete mind map for a session.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    # Fetch nodes
    nodes_result = await db.execute(select(MindmapNode).where(MindmapNode.session_id == session_uuid))
    db_nodes = nodes_result.scalars().all()

    # Fetch edges
    edges_result = await db.execute(select(MindmapEdge).where(MindmapEdge.session_id == session_uuid))
    db_edges = edges_result.scalars().all()

    nodes = []
    for n in db_nodes:
        nodes.append({
            "id": str(n.id),
            "session_id": str(n.session_id),
            "parent_id": str(n.parent_id) if n.parent_id else None,
            "type": n.type,
            "label": n.label,
            "description": n.description,
            "position_x": float(n.position_x),
            "position_y": float(n.position_y),
            "order_index": n.order_index,
        })

    edges = []
    for e in db_edges:
        edges.append({
            "id": str(e.id),
            "session_id": str(e.session_id),
            "source_node_id": str(e.source_node_id),
            "target_node_id": str(e.target_node_id),
            "relationship_type": e.relationship_type,
        })

    return {
        "session_id": session_id,
        "nodes": nodes,
        "edges": edges,
    }
