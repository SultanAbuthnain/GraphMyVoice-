"""
app/models/task.py
───────────────────
SQLAlchemy ORM model for the `tasks` table.
One-to-one with MindmapNode (only for nodes of type='task').
"""

from datetime import date
from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    node_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("mindmap_nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Relationship back to node
    node: Mapped["MindmapNode"] = relationship(  # type: ignore[name-defined]
        "MindmapNode", back_populates="task"
    )
