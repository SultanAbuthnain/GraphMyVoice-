"""
app/api/v1/tasks.py
────────────────────
Endpoint:
  PATCH /tasks/{node_id}  → toggle task checked/unchecked, update due date/owner
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.deps import UserPayload, get_current_user, get_db

router = APIRouter()


class TaskUpdateRequest(BaseModel):
    is_checked: bool | None = None
    due_date: str | None = None
    owner: str | None = None


@router.patch("/{node_id}", status_code=status.HTTP_200_OK)
async def update_task(
    node_id: str,
    body: TaskUpdateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """Toggle task completion and optionally update due date / owner."""
    # TODO: query tasks table by node_id, verify ownership, update fields
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "node_id": node_id,
        "is_checked": body.is_checked,
        "due_date": body.due_date,
        "owner": body.owner,
        "updated_at": now,
    }
