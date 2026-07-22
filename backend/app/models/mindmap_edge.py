"""
app/models/mindmap_edge.py
───────────────────────────
SQLAlchemy ORM model for the `mindmap_edges` table.
Cross-links beyond the parent/child tree extracted by the AI.
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MindmapEdge(Base):
    __tablename__ = "mindmap_edges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False, default="relates_to")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="edges")  # type: ignore[name-defined]
    
    source_node: Mapped["MindmapNode"] = relationship(  # type: ignore[name-defined]
        "MindmapNode", foreign_keys=[source_node_id], back_populates="outgoing_edges"
    )
    target_node: Mapped["MindmapNode"] = relationship(  # type: ignore[name-defined]
        "MindmapNode", foreign_keys=[target_node_id], back_populates="incoming_edges"
    )
