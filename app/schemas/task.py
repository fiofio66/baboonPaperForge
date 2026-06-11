"""
Pydantic v2 schemas for TaskRecord CRUD.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared fields
# ---------------------------------------------------------------------------
class TaskBase(BaseModel):
    journal_name: str = Field(..., max_length=256)
    template_format: str = Field(..., max_length=16, examples=["latex"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------
class TaskCreate(TaskBase):
    """Create a new typesetting task."""
    user_config_id: UUID | None = None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------
class TaskUpdate(BaseModel):
    """Update task fields (e.g., status transitions, attach mapping JSON)."""
    status: str | None = Field(None, max_length=32)
    template_metadata_id: UUID | None = None
    mapping_json: str | None = None
    output_path: str | None = Field(None, max_length=512)
    error_message: str | None = None
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------
class TaskRead(TaskBase):
    id: UUID
    user_config_id: UUID | None
    status: str
    template_metadata_id: UUID | None
    mapping_json: str | None
    output_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
