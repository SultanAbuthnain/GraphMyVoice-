"""
app/models/mindmap_node.py
───────────────────────────
SQLAlchemy ORM model for the `mindmap_nodes` table.
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, Text, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MindmapNode(Base):
    __tablename__ = "mindmap_nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), nullable=True, index=True
    )

    type: Mapped[str] = mapped_column(
        Enum("goal", "plan", "task", "topic", "note_ref", name="node_type"),
        nullable=False,
        default="topic"
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    position_x: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    position_y: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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
    session: Mapped["Session"] = relationship("Session", back_populates="nodes")  # type: ignore[name-defined]
    
    # Self-referential
    parent: Mapped["MindmapNode"] = relationship(
        "MindmapNode", back_populates="children", remote_side=[id]
    )
    children: Mapped[list["MindmapNode"]] = relationship(
        "MindmapNode", back_populates="parent", cascade="all, delete-orphan"
    )

    # Cross-links where this node is source or target
    outgoing_edges: Mapped[list["MindmapEdge"]] = relationship(  # type: ignore[name-defined]
        "MindmapEdge", foreign_keys="[MindmapEdge.source_node_id]", back_populates="source_node", cascade="all, delete-orphan"
    )
    incoming_edges: Mapped[list["MindmapEdge"]] = relationship(  # type: ignore[name-defined]
        "MindmapEdge", foreign_keys="[MindmapEdge.target_node_id]", back_populates="target_node", cascade="all, delete-orphan"
    )

    task_item: Mapped["Task"] = relationship(  # type: ignore[name-defined]
        "Task", back_populates="node", uselist=False, cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(  # type: ignore[name-defined]
        "Note", back_populates="node", cascade="all, delete-orphan"
    )
