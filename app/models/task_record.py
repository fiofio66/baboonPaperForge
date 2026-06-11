"""
ORM model: TaskRecord

Tracks the full lifecycle of a LangGraph typesetting workflow run:
search → analyze → await user input → assemble → complete/fail.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskRecord(Base):
    __tablename__ = "task_record"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_config.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    journal_name: Mapped[str] = mapped_column(
        String(256), nullable=False, index=True
    )
    template_format: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="latex | docx"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
        comment="pending|searching|analyzing|awaiting_input|assembling|completed|failed",
    )
    template_metadata_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_metadata.id", ondelete="SET NULL"),
        nullable=True,
    )
    mapping_json: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Analyst Agent mapping JSON"
    )
    output_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Path to compiled output"
    )
    error_message: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Error detail if status == failed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<TaskRecord {self.journal_name} [{self.status}]>"
