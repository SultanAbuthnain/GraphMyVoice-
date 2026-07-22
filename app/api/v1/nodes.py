"""
app/api/v1/nodes.py
────────────────────
Endpoint:
  PATCH /nodes/{id}  → edit node label or request branch regeneration
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import UserPayload, get_current_user, get_db

router = APIRouter()


class NodeUpdateRequest(BaseModel):
    label: str | None = None
    regenerate_branch: bool = False


@router.patch("/{node_id}", status_code=status.HTTP_200_OK)
async def update_node(
    node_id: str,
    body: NodeUpdateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Edit a node's label, or trigger branch regeneration via LangGraph HITL.
    """
    # TODO: query mindmap_nodes table, verify ownership via session, update label
    # TODO: if regenerate_branch=True, enqueue a regen job and return job_id
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if body.regenerate_branch:
        return {
            "id": node_id,
            "label": body.label,
            "updated_at": now,
            "regeneration_job_id": f"regen_{node_id[:8]}",
            "message": "جاري إعادة توليد الفرع، تابع الحالة عبر /sessions/{id}/status",
        }

    return {
        "id": node_id,
        "label": body.label,
        "updated_at": now,
        "regeneration_job_id": None,
    }
