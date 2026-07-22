"""
app/models/session.py
──────────────────────
SQLAlchemy ORM model for the `sessions` table.
Tracks the lifecycle of one audio processing job.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    audio_path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="auto")

    # Pipeline state
    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        nullable=False,
        # possible values: queued | transcribing | extracting |
        #                  building_mindmap | validating | saving | done | failed
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String(32), default="ingestion")

    # Optional step-by-step details stored as JSONB
    steps_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Transcript (stored after Whisper completes)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
