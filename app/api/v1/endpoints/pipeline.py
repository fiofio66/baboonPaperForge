"""
Preview & export endpoints.

POST /api/v1/preview          — real-time preview of assembled content
POST /api/v1/export/pdf       — compile .tex to PDF and return download
POST /api/v1/export/tex       — return assembled .tex source
POST /api/v1/pipeline/run     — run the full multi-agent pipeline
GET  /api/v1/pipeline/status  — check pipeline progress
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.assemble import AssembleRequest, AssembleResponse, FigureConfig
from app.schemas.mapping import TemplateMapping
from app.services.assembler import assemble_template

router = APIRouter(prefix="", tags=["pipeline"])


# ---------------------------------------------------------------------------
# Pipeline run
# ---------------------------------------------------------------------------
class PipelineRequest(BaseModel):
    journal_name: str = Field(..., examples=["IEEE Internet of Things Journal"])
    template_format: str = Field(default="latex")
    template_path: str = Field(default="")
    user_content: dict[str, str] = Field(default_factory=dict)
    figures: list[dict] = Field(default_factory=list)
    user_config_id: str | None = None


class PipelineResponse(BaseModel):
    task_id: str
    status: str
    agent_log: list[str]
    template_path: str
    mapping_json: str | None
    parse_used_llm: bool
    rag_constraints: list[dict]
    assembled_text: str | None
    output_path: str | None
    error: str | None


_recent_pipelines: dict[str, dict] = {}


@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(payload: PipelineRequest, db: AsyncSession = Depends(get_db)):
    """Run the full multi-agent pipeline: Search → Parse → RAG → Assemble."""
    import asyncio

    task_id = uuid.uuid4().hex[:12]

    # If user_config_id provided, load LLM config for fallback
    llm_config = None
    if payload.user_config_id:
        from uuid import UUID
        from app.services.user_config_service import (
            get_user_config_with_llm_configs,
            get_active_llm_config,
        )
        uid = UUID(payload.user_config_id)
        user = await get_user_config_with_llm_configs(db, uid)
        if user and user.llm_configs:
            active = [c for c in user.llm_configs if c.is_active]
            if active:
                cfg = active[0]
                llm_config = {
                    "provider": cfg.provider,
                    "api_key": cfg.api_key_encrypted or "",
                    "base_url": cfg.base_url or "",
                    "model_name": cfg.model_name or "",
                }

    async def _run():
        from app.agents.supervisor import run_pipeline as run
        try:
            result = await run(
                journal_name=payload.journal_name,
                template_format=payload.template_format,
                mode="full_pipeline",
                template_path=payload.template_path,
                user_content=payload.user_content,
                figures=payload.figures,
                llm_config=llm_config,
            )
            _recent_pipelines[task_id] = dict(result)
        except Exception as exc:
            _recent_pipelines[task_id] = {"status": "failed", "error": str(exc), "agent_log": []}

    asyncio.create_task(_run())

    return PipelineResponse(
        task_id=task_id,
        status="running",
        agent_log=[f"Pipeline started for '{payload.journal_name}'"],
        template_path="",
        mapping_json=None,
        parse_used_llm=False,
        rag_constraints=[],
        assembled_text=None,
        output_path=None,
        error=None,
    )


@router.get("/pipeline/status", response_model=PipelineResponse)
async def pipeline_status(task_id: str = Query(...)):
    """Poll for pipeline results."""
    data = _recent_pipelines.get(task_id)
    if not data:
        raise HTTPException(404, "Task not found")
    return PipelineResponse(
        task_id=task_id,
        status=data.get("status", "unknown"),
        agent_log=data.get("agent_log", []),
        template_path=data.get("template_path", ""),
        mapping_json=data.get("mapping_json"),
        parse_used_llm=data.get("parse_used_llm", False),
        rag_constraints=data.get("rag_constraints", []),
        assembled_text=data.get("assembled_text"),
        output_path=data.get("output_path"),
        error=data.get("error"),
    )


# ---------------------------------------------------------------------------
# Preview (real-time, no DB needed)
# ---------------------------------------------------------------------------
class PreviewRequest(BaseModel):
    template_path: str
    template_format: str = "latex"
    mapping_json: str
    user_content: dict[str, str] = Field(default_factory=dict)
    figures: list[dict] = Field(default_factory=list)


class PreviewResponse(BaseModel):
    assembled_text: str
    line_count: int


@router.post("/preview", response_model=PreviewResponse)
async def preview_assemble(payload: PreviewRequest):
    """Generate a live preview of the assembled document.

    This is read-only — no files are written, no DB calls.
    """
    from app.schemas.mapping import TemplateMapping
    from app.services.latex_assembler import assemble_latex
    from app.services.docx_assembler import assemble_docx

    mapping = TemplateMapping.model_validate_json(payload.mapping_json)

    if payload.template_format in ("latex", "tex"):
        text = assemble_latex(
            payload.template_path, mapping,
            payload.user_content,
            figures=payload.figures,
        )
    else:
        doc = assemble_docx(payload.template_path, mapping, payload.user_content)
        text = "\n\n".join(p.text for p in doc.paragraphs)

    return PreviewResponse(
        assembled_text=text,
        line_count=text.count("\n") + 1,
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
@router.post("/export/tex")
async def export_tex(payload: PreviewRequest):
    """Download the assembled .tex file."""
    from app.schemas.mapping import TemplateMapping
    from app.services.latex_assembler import assemble_latex
    from fastapi.responses import PlainTextResponse

    mapping = TemplateMapping.model_validate_json(payload.mapping_json)
    text = assemble_latex(
        payload.template_path, mapping,
        payload.user_content,
        figures=payload.figures,
    )

    safe_name = Path(payload.template_path).stem or "paper"
    return PlainTextResponse(
        text,
        media_type="application/x-tex",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_assembled.tex"'},
    )


@router.post("/export/pdf")
async def export_pdf(payload: PreviewRequest):
    """Compile the assembled .tex to PDF and download it.

    Requires pdflatex in PATH. Returns the .tex file if compilation fails.
    """
    from app.schemas.mapping import TemplateMapping
    from app.services.latex_assembler import assemble_latex
    from fastapi.responses import FileResponse, PlainTextResponse

    mapping = TemplateMapping.model_validate_json(payload.mapping_json)
    assembled = assemble_latex(
        payload.template_path, mapping,
        payload.user_content,
        figures=payload.figures,
    )

    # Write to temp dir and compile
    tmpdir = Path(tempfile.mkdtemp())
    tex_path = tmpdir / "paper.tex"
    tex_path.write_text(assembled, encoding="utf-8")

    # Copy template resources (cls, sty, images) to temp dir
    template_dir = Path(payload.template_path).parent
    for ext in [".cls", ".sty", ".bst", ".bib"]:
        for f in template_dir.glob(f"*{ext}"):
            shutil.copy2(f, tmpdir / f.name)
    # Copy figures directory if exists
    fig_dir = template_dir / "figures"
    if fig_dir.is_dir():
        shutil.copytree(fig_dir, tmpdir / "figures", dirs_exist_ok=True)

    try:
        # Run pdflatex twice for references
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "paper.tex"],
                cwd=str(tmpdir),
                capture_output=True,
                text=True,
                timeout=60,
            )
        pdf_path = tmpdir / "paper.pdf"
        if pdf_path.exists():
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"{Path(payload.template_path).stem}_assembled.pdf",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: return .tex
    return PlainTextResponse(
        assembled,
        media_type="application/x-tex",
        headers={"Content-Disposition": f'attachment; filename="{Path(payload.template_path).stem}_assembled.tex"'},
    )
