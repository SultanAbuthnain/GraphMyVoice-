"""
app/models/mindmap_node.py
───────────────────────────
SQLAlchemy ORM model for the `mindmap_nodes` table.
One row per node in the mind map (root, goal, plan, or task).
"""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MindmapNode(Base):
    __tablename__ = "mindmap_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("mindmap_nodes.id", ondelete="SET NULL"), nullable=True
    )

    label: Mapped[str] = mapped_column(Text, nullable=False)
    node_type: Mapped[str] = mapped_column(
        String(16), nullable=False
        # Values: root | goal | plan | task
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamp reference back to the transcript (for hallucination check)
    source_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g. {"timestamp_start": "00:01:30", "timestamp_end": "00:02:45"}

    # Relationships
    task: Mapped["Task"] = relationship(  # type: ignore[name-defined]
        "Task", back_populates="node", uselist=False, cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(  # type: ignore[name-defined]
        "Note", back_populates="node", cascade="all, delete-orphan"
    )
