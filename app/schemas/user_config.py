"""
Pydantic v2 schemas for UserConfig & LLMConfig CRUD.

SECURITY: LLMConfigRead.api_key_encrypted always returns "********".
The plaintext API key is accepted on create/update but NEVER exposed on read.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


# ======================================================================
# UserConfig
# ======================================================================

class UserConfigBase(BaseModel):
    user_identifier: str = Field(..., max_length=256, examples=["alice@example.com"])
    default_provider: str = Field(default="openai", max_length=32)


class UserConfigCreate(UserConfigBase):
    """Create a new user configuration (idempotent by user_identifier)."""
    pass


class UserConfigUpdate(BaseModel):
    default_provider: str | None = Field(None, max_length=32)


class UserConfigRead(UserConfigBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# LLMConfig
# ======================================================================

class LLMConfigBase(BaseModel):
    provider: str = Field(..., max_length=32, examples=["openai"])
    base_url: str | None = Field(None, max_length=512)
    model_name: str | None = Field(None, max_length=128)
    is_active: bool = True


class LLMConfigCreate(LLMConfigBase):
    """Create a new LLM provider config. `api_key` is plaintext — the service
    layer encrypts it before persistence."""
    api_key: str | None = Field(
        None, max_length=512, examples=["sk-abc123..."],
        description="Plaintext API key (NULL for ollama). Encrypted at rest."
    )


class LLMConfigUpdate(BaseModel):
    provider: str | None = Field(None, max_length=32)
    api_key: str | None = Field(
        None, max_length=512,
        description="New plaintext API key. If provided, re-encrypts and overwrites."
    )
    base_url: str | None = Field(None, max_length=512)
    model_name: str | None = Field(None, max_length=128)
    is_active: bool | None = None


class LLMConfigRead(LLMConfigBase):
    id: UUID
    user_config_id: UUID
    api_key_encrypted: Annotated[
        str | None,
        Field(description="ALWAYS masked — never returns real key"),
    ] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("api_key_encrypted")
    def _mask_api_key(self, value: str | None) -> str | None:
        """Replace any stored value with a fixed mask to prevent leakage."""
        if value is not None and value != "":
            return "********"
        return value


# ======================================================================
# Composite response — user + their LLM configs
# ======================================================================

class UserConfigWithLLMs(UserConfigRead):
    llm_configs: list[LLMConfigRead] = []

    model_config = ConfigDict(from_attributes=True)
