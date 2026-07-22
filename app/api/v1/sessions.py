"""
app/api/v1/sessions.py
───────────────────────
Endpoints:
  POST   /sessions/upload        → upload audio, kick off pipeline
  GET    /sessions               → list user's sessions
  GET    /sessions/{id}/status   → poll pipeline progress
"""

import os
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import UserPayload, get_current_user, get_db
from app.config import get_settings

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
    file: UploadFile = File(...),
    title: str = Form(...),
    language: str = Form(default="auto"),
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Upload an audio file and start the LangGraph pipeline asynchronously.
    Returns 202 immediately; client should poll /sessions/{id}/status.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    allowed = settings.allowed_audio_types_list
    content_type = file.content_type or ""
    filename = file.filename or ""

    if content_type not in allowed and not any(
        filename.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".ogg"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_file",
                "message": "نوع الملف غير مدعوم. الأنواع المقبولة: mp3, wav, m4a, ogg",
                "code": 400,
            },
        )

    # ── Validate file size ────────────────────────────────────────────────────
    # Read a chunk to check; multipart doesn't expose size directly
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "file_too_large",
                "message": f"حجم الملف يتجاوز الحد المسموح ({settings.max_file_size_mb}MB)",
                "code": 413,
            },
        )

    # ── Generate session ID and save file ─────────────────────────────────────
    session_id = f"sess_{uuid.uuid4().hex[:24].upper()}"
    ext = os.path.splitext(filename)[-1] or ".audio"
    audio_path = os.path.join(settings.upload_dir, f"{session_id}{ext}")

    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(content)

    # ── TODO: Create session row in DB ────────────────────────────────────────
    # session = Session(id=session_id, user_id=current_user.user_id, ...)
    # db.add(session); await db.commit()

    # ── TODO: Start background pipeline ──────────────────────────────────────
    # background_tasks.add_task(run_pipeline, session_id, audio_path, current_user.user_id, language)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "session_id": session_id,
        "title": title,
        "status": "queued",
        "created_at": now,
        "estimated_duration_seconds": 120,
        "message": "تم استلام الملف وبدأت المعالجة",
        "poll_url": f"/api/v1/sessions/{session_id}/status",
    }


# ─────────────────────────────────────────────────────────────────────────────
#  GET /sessions
# ─────────────────────────────────────────────────────────────────────────────
@router.get("", status_code=status.HTTP_200_OK)
async def list_sessions(
    page: int = 1,
    limit: int = 10,
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """Return paginated list of the current user's sessions."""
    # TODO: query DB for real sessions
    # Mock response matching api-contract.md §7
    return {
        "sessions": [
            {
                "id": "sess_MOCK000000000000000001",
                "title": "محاضرة البرمجة - الأسبوع الأول",
                "status": "done",
                "created_at": "2026-07-22T21:00:00Z",
                "stats": {"total_tasks": 4, "tasks_completed": 1},
            },
            {
                "id": "sess_MOCK000000000000000002",
                "title": "اجتماع الفريق - التخطيط",
                "status": "transcribing",
                "created_at": "2026-07-22T20:00:00Z",
                "stats": None,
            },
        ],
        "total": 2,
        "page": page,
        "limit": limit,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  GET /sessions/{id}/status
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{session_id}/status", status_code=status.HTTP_200_OK)
async def get_session_status(
    session_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Poll the pipeline progress for a given session.
    Client should poll every 3 seconds until status is 'done' or 'failed'.
    """
    # TODO: query sessions table and return real status
    # Mock: always returns 'transcribing' at 25%
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "session_id": session_id,
        "status": "transcribing",
        "progress_percent": 25,
        "current_step": "transcribing",
        "steps": [
            {"name": "ingestion",       "label": "استلام الملف",         "status": "done",        "completed_at": "2026-07-22T21:00:05Z"},
            {"name": "transcribing",    "label": "تفريغ الصوت",          "status": "in_progress", "completed_at": None},
            {"name": "extracting",      "label": "استخراج المحتوى",      "status": "pending",     "completed_at": None},
            {"name": "building_mindmap","label": "بناء الخريطة الذهنية", "status": "pending",     "completed_at": None},
            {"name": "validating",      "label": "التحقق من الجودة",     "status": "pending",     "completed_at": None},
            {"name": "saving",          "label": "حفظ النتائج",          "status": "pending",     "completed_at": None},
        ],
        "started_at": "2026-07-22T21:00:03Z",
        "updated_at": now,
        "error": None,
    }
