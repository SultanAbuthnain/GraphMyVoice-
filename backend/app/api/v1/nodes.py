"""
app/api/v1/nodes.py
────────────────────
Endpoint:
  PATCH /sessions/{session_id}/nodes/{node_id}  → edit node label/position
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserPayload, get_current_user, get_db
from app.models.mindmap_node import MindmapNode

router = APIRouter()


class NodeUpdateRequest(BaseModel):
    label: str | None = None
    position_x: float | None = None
    position_y: float | None = None


@router.patch("/{session_id}/nodes/{node_id}", status_code=status.HTTP_200_OK)
async def update_node(
    session_id: str,
    node_id: str,
    body: NodeUpdateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Edit a node's label or update its layout coordinates.
    """
    try:
        sess_uuid = uuid.UUID(session_id)
        node_uuid = uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(MindmapNode).where(MindmapNode.id == node_uuid, MindmapNode.session_id == sess_uuid)
    )
    db_node = result.scalars().first()
    
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")

    if body.label is not None:
        db_node.label = body.label
    if body.position_x is not None:
        db_node.position_x = body.position_x
    if body.position_y is not None:
        db_node.position_y = body.position_y

    await db.commit()
    await db.refresh(db_node)

    return {
        "id": str(db_node.id),
        "session_id": str(db_node.session_id),
        "parent_id": str(db_node.parent_id) if db_node.parent_id else None,
        "type": db_node.type,
        "label": db_node.label,
        "description": db_node.description,
        "position_x": float(db_node.position_x),
        "position_y": float(db_node.position_y),
        "order_index": db_node.order_index,
    }
