"""
app/api/v1/notes.py
────────────────────
Endpoint:
  POST /nodes/{id}/notes  → add a note to a node
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.deps import UserPayload, get_current_user, get_db

router = APIRouter()


class NoteCreateRequest(BaseModel):
    content: str


@router.post("/{node_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_note(
    node_id: str,
    body: NoteCreateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """Add a personal note to any mind map node."""
    # TODO: verify node exists and belongs to a session owned by current_user
    # TODO: insert into notes table
    note_id = f"note_{uuid.uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "id": note_id,
        "node_id": node_id,
        "user_id": current_user.user_id,
        "content": body.content,
        "created_at": now,
    }
