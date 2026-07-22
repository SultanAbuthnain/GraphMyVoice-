"""
app/api/v1/sessions.py
───────────────────────
Endpoints:
  POST   /sessions/upload        → upload audio, kick off pipeline
  GET    /sessions               → list user's sessions
  GET    /sessions/{id}/status   → poll pipeline progress
"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import UserPayload, get_current_user, get_db
from app.config import get_settings
from app.models.session import Session
from app.services.pipeline_service import run_pipeline

settings = get_settings()
router = APIRouter()

# ── Upload rate limiter: 3 uploads / hour / IP ───────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─────────────────────────────────────────────────────────────────────────────
#  POST /sessions/upload
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(f"{settings.rate_limit_uploads_per_hour}/hour")
async def upload_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    title: str = Form(default="Untitled session"),
    language: str = Form(default="auto"),
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an audio file and start the LangGraph pipeline asynchronously.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    allowed = settings.allowed_audio_types_list
    content_type = audio.content_type or ""
    filename = audio.filename or ""

    if content_type not in allowed and not any(
        filename.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".ogg", ".webm"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="نوع الملف غير مدعوم. الأنواع المقبولة: mp3, wav, m4a, webm",
        )

    # ── Read file ─────────────────────────────────────────────────────────────
    content = await audio.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"حجم الملف يتجاوز الحد المسموح ({settings.max_file_size_mb}MB)",
        )

    # ── Generate session ID and save file ─────────────────────────────────────
    session_id = uuid.uuid4()
    ext = os.path.splitext(filename)[-1] or ".audio"
    # Audio URL logic (just save it locally and store the path for now)
    audio_path = os.path.join(settings.upload_dir, f"{session_id.hex}{ext}")

    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(content)

    # ── Create session row in DB ──────────────────────────────────────────────
    db_session = Session(
        id=session_id,
        title=title,
        status="uploaded",
        audio_url=audio_path,
        duration_sec=None,
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    # ── Start background pipeline ─────────────────────────────────────────────
    background_tasks.add_task(run_pipeline, str(session_id), audio_path, current_user.user_id, language)

    return {
        "id": str(db_session.id),
        "title": db_session.title,
        "status": db_session.status,
        "error_message": db_session.error_message,
        "audio_url": db_session.audio_url,
        "duration_sec": float(db_session.duration_sec) if db_session.duration_sec else None,
        "created_at": db_session.created_at.isoformat(),
        "updated_at": db_session.updated_at.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  GET /sessions
# ─────────────────────────────────────────────────────────────────────────────
@router.get("", status_code=status.HTTP_200_OK)
async def list_sessions(
    page: int = 1,
    limit: int = 10,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated list of sessions."""
    # Simple real DB query
    result = await db.execute(
        select(Session).order_by(Session.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    sessions = result.scalars().all()
    
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "status": s.status,
            "error_message": s.error_message,
            "audio_url": s.audio_url,
            "duration_sec": float(s.duration_sec) if s.duration_sec else None,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        } for s in sessions
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  GET /sessions/{id}/status
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{session_id}/status", status_code=status.HTTP_200_OK)
async def get_session_status(
    session_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Poll the pipeline progress for a given session.
    """
    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
    s = result.scalars().first()
    
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(s.id),
        "title": s.title,
        "status": s.status,
        "error_message": s.error_message,
        "audio_url": s.audio_url,
        "duration_sec": float(s.duration_sec) if s.duration_sec else None,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }
