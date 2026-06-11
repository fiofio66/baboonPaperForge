"""
Pydantic v2 schemas for TemplateMetadata CRUD.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared fields
# ---------------------------------------------------------------------------
class TemplateBase(BaseModel):
    journal_name: str = Field(..., max_length=256, examples=["IEEE Internet of Things Journal"])
    template_format: str = Field(..., max_length=16, examples=["latex"])
    version: str | None = Field(None, max_length=64)
    download_path: str = Field(..., max_length=512)
    mapping_json: str | None = None


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
class TemplateCreate(TemplateBase):
    """Payload for creating a new template metadata record."""
    pass


# ---------------------------------------------------------------------------
# Update (partial)
# ---------------------------------------------------------------------------
class TemplateUpdate(BaseModel):
    journal_name: str | None = Field(None, max_length=256)
    template_format: str | None = Field(None, max_length=16)
    version: str | None = Field(None, max_length=64)
    download_path: str | None = Field(None, max_length=512)
    mapping_json: str | None = None


# ---------------------------------------------------------------------------
# Read (response)
# ---------------------------------------------------------------------------
class TemplateRead(TemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
