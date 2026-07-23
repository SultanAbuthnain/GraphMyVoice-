"""
app/models/session.py
──────────────────────
SQLAlchemy ORM model for the `sessions` table.
Tracks the lifecycle of one audio processing job.
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, Index, Numeric, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Owner of this session — used for multi-tenant data isolation
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="Untitled session")
    
    status: Mapped[str] = mapped_column(
        Enum(
            "uploaded", "transcribing", "extracting", "structuring", "validating", "completed", "failed",
            name="session_status"
        ),
        default="uploaded",
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    duration_sec: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    nodes: Mapped[list["MindmapNode"]] = relationship(  # type: ignore[name-defined]
        "MindmapNode", back_populates="session", cascade="all, delete-orphan"
    )
    edges: Mapped[list["MindmapEdge"]] = relationship(  # type: ignore[name-defined]
        "MindmapEdge", back_populates="session", cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(  # type: ignore[name-defined]
        "Note", back_populates="session", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task", back_populates="session", cascade="all, delete-orphan"
    )
