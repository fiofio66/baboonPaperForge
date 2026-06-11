"""
ORM models: UserConfig & LLMConfig

BYOK multi-tenant configuration:
- UserConfig: opaque user identity + default provider preference
- LLMConfig:  encrypted API key per provider per user (Fernet at rest)

Security: `api_key_encrypted` stores `encrypt(plaintext_key)`.
It must NEVER be returned in plaintext from any API response.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserConfig(Base):
    __tablename__ = "user_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_identifier: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False, index=True
    )
    default_provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="openai"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ---- relationships ----
    llm_configs: Mapped[list["LLMConfig"]] = relationship(
        "LLMConfig",
        back_populates="user_config",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserConfig {self.user_identifier}>"


class LLMConfig(Base):
    __tablename__ = "llm_config"
    __table_args__ = (
        UniqueConstraint("user_config_id", "provider", name="uq_llm_config_user_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_config.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="openai | anthropic | gemini | ollama"
    )
    api_key_encrypted: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Fernet-encrypted API key; NULL for ollama"
    )
    base_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Custom endpoint override"
    )
    model_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment='e.g. "gpt-4o", "claude-opus-4-8"'
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ---- relationships ----
    user_config: Mapped["UserConfig"] = relationship(
        "UserConfig", back_populates="llm_configs"
    )

    def __repr__(self) -> str:
        return f"<LLMConfig {self.provider} for user_config_id={self.user_config_id}>"
