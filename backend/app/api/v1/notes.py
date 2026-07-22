"""
app/api/v1/notes.py
────────────────────
Endpoints:
  GET    /sessions/{session_id}/notes
  POST   /sessions/{session_id}/notes
  DELETE /sessions/{session_id}/notes/{note_id}
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserPayload, get_current_user, get_db
from app.models.note import Note
from app.models.session import Session

router = APIRouter()


class NoteCreateRequest(BaseModel):
    content: str
    node_id: str | None = None


@router.get("/{session_id}/notes", status_code=status.HTTP_200_OK)
async def list_notes(
    session_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    result = await db.execute(select(Note).where(Note.session_id == sess_uuid))
    db_notes = result.scalars().all()
    
    return [
        {
            "id": str(n.id),
            "session_id": str(n.session_id),
            "node_id": str(n.node_id) if n.node_id else None,
            "content": n.content,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in db_notes
    ]


@router.post("/{session_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_note(
    session_id: str,
    body: NoteCreateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    db_note = Note(
        session_id=sess_uuid,
        node_id=uuid.UUID(body.node_id) if body.node_id else None,
        content=body.content,
    )
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)

    return {
        "id": str(db_note.id),
        "session_id": str(db_note.session_id),
        "node_id": str(db_note.node_id) if db_note.node_id else None,
        "content": db_note.content,
        "created_at": db_note.created_at.isoformat(),
        "updated_at": db_note.updated_at.isoformat(),
    }


@router.delete("/{session_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    session_id: str,
    note_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sess_uuid = uuid.UUID(session_id)
        note_uuid = uuid.UUID(note_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(Note).where(Note.id == note_uuid, Note.session_id == sess_uuid)
    )
    db_note = result.scalars().first()
    
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    await db.delete(db_note)
    await db.commit()
