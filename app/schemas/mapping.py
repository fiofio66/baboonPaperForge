"""
Pydantic models for the template module mapping (Analyst Agent output).

This is the central data structure that bridges template analysis (Phase 3)
and the zero-token assembler (Phase 5).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModuleConstraint(BaseModel):
    """A formatting constraint pulled from RAG / Author Guidelines."""
    key: str = Field(..., examples=["max_words", "citation_style"])
    value: str = Field(..., examples=["250", "IEEE numeric"])
    source: str | None = Field(None, examples=["Author Guidelines §3.2"])


class ModuleMapping(BaseModel):
    """A single module entry in the template structure tree."""
    id: str = Field(..., examples=["mod-001"])
    type: str = Field(..., examples=["title", "abstract", "section", "bibliography", "figure"])
    label: str = Field(..., examples=["Introduction"])
    anchor_line: int | None = Field(None, description="Line number in .tex; para_index for .docx")
    anchor_type: str = Field(..., examples=["regex", "environment", "heading_style", "placeholder"])
    anchor_pattern: str = Field(
        ..., description="Regex or style name used to locate this module in the template"
    )
    content: str = Field("", description="Original template placeholder text at anchor")
    level: int | None = Field(None, description="Section nesting level (1=section, 2=subsection)")
    constraints: list[ModuleConstraint] = Field(default_factory=list)


class TemplateMapping(BaseModel):
    """Complete module structure for a parsed template."""
    template_path: str
    format: str = Field(..., examples=["latex", "docx"])
    modules: list[ModuleMapping] = Field(default_factory=list)

    @property
    def section_count(self) -> int:
        return sum(1 for m in self.modules if m.type == "section")

    @property
    def module_ids(self) -> list[str]:
        return [m.id for m in self.modules]
