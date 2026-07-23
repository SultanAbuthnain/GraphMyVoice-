"""
app/api/v1/tasks.py
────────────────────
Endpoints:
  GET    /sessions/{session_id}/tasks
  POST   /sessions/{session_id}/tasks
  PATCH  /sessions/{session_id}/tasks/{task_id}

All endpoints verify that the target session belongs to the authenticated
user before reading or mutating any data.
"""

import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserPayload, get_current_user, get_db
from app.api.v1.sessions import _get_owned_session
from app.models.task import Task

router = APIRouter()


class TaskUpdateRequest(BaseModel):
    is_done: bool


class TaskCreateRequest(BaseModel):
    title: str
    node_id: str | None = None
    due_date: date | None = None


@router.get("/{session_id}/tasks", status_code=status.HTTP_200_OK)
async def list_tasks(
    session_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all tasks for a session.
    Returns 403 if the session belongs to a different user.
    """
    # Ownership check — raises 404/403 as appropriate
    await _get_owned_session(session_id, current_user, db)

    sess_uuid = uuid.UUID(session_id)
    result = await db.execute(select(Task).where(Task.session_id == sess_uuid))
    db_tasks = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "session_id": str(t.session_id),
            "node_id": str(t.node_id) if t.node_id else None,
            "title": t.title,
            "is_done": t.is_done,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in db_tasks
    ]


@router.patch("/{session_id}/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def toggle_task(
    session_id: str,
    task_id: str,
    body: TaskUpdateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle the done-state of a task.
    Returns 403 if the session belongs to a different user.
    """
    # Ownership check — raises 404/403 as appropriate
    await _get_owned_session(session_id, current_user, db)

    try:
        sess_uuid = uuid.UUID(session_id)
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(Task).where(Task.id == task_uuid, Task.session_id == sess_uuid)
    )
    db_task = result.scalars().first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.is_done = body.is_done
    await db.commit()
    await db.refresh(db_task)

    return {
        "id": str(db_task.id),
        "session_id": str(db_task.session_id),
        "node_id": str(db_task.node_id) if db_task.node_id else None,
        "title": db_task.title,
        "is_done": db_task.is_done,
        "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
    }


@router.post("/{session_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    session_id: str,
    body: TaskCreateRequest,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a task to a session.
    Returns 403 if the session belongs to a different user.
    """
    # Ownership check — raises 404/403 as appropriate
    await _get_owned_session(session_id, current_user, db)

    sess_uuid = uuid.UUID(session_id)
    db_task = Task(
        session_id=sess_uuid,
        node_id=uuid.UUID(body.node_id) if body.node_id else None,
        title=body.title,
        due_date=body.due_date,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return {
        "id": str(db_task.id),
        "session_id": str(db_task.session_id),
        "node_id": str(db_task.node_id) if db_task.node_id else None,
        "title": db_task.title,
        "is_done": db_task.is_done,
        "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
    }
