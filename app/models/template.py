"""
ORM model: TemplateMetadata

Stores downloaded template info (journal name, version, local path, format).
This is a skeleton — fields will be enriched in later iterations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TemplateMetadata(Base):
    __tablename__ = "template_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    journal_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    template_format: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="latex | docx"
    )
    version: Mapped[str] = mapped_column(String(64), nullable=True)
    download_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mapping_json: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="JSON placeholder map from Analyst Agent"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<TemplateMetadata {self.journal_name} [{self.template_format}]>"
