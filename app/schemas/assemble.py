"""
Pydantic schemas for the Zero-Token Assembler.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FigureConfig(BaseModel):
    """Configuration for a single figure/table to inject."""
    caption: str = Field(..., examples=["System architecture diagram"])
    label: str = Field(..., examples=["fig:arch"])
    image_path: str = Field("", examples=["figures/arch.png"])
    is_wide: bool = Field(False, description="Use figure*/table* (cross-column)")
    width: str = Field(r"\columnwidth", description="LaTeX width spec")
    content: str = Field("", description="Tabular content for tables")


class AssembleRequest(BaseModel):
    """Payload for the assemble endpoint."""
    template_id: str = Field(..., examples=["550e8400-e29b-41d4-a716-446655440000"])
    user_content: dict[str, str] = Field(
        ...,
        description="module_id → content mapping (plain text)",
        examples=[{"mod-001": "My Paper Title", "mod-003": "This paper explores..."}],
    )
    figures: list[FigureConfig] = Field(default_factory=list)


class AssembleResponse(BaseModel):
    """Result of an assembly operation."""
    status: str
    template_id: str
    output_path: str
    output_format: str
    module_count: int
    filled_count: int
