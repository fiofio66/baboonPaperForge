"""
Preview, render & export — Overleaf-like real-time compilation.

POST /api/v1/preview/text        — raw assembled LaTeX source
POST /api/v1/preview/render      — compile to PDF, return as base64 for inline preview
POST /api/v1/export/pdf          — download compiled PDF
POST /api/v1/export/tex          — download .tex source
POST /api/v1/pipeline/run        — full multi-agent pipeline
GET  /api/v1/pipeline/status     — poll pipeline progress
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.mapping import TemplateMapping

router = APIRouter(prefix="", tags=["pipeline"])


# ===================================================================
# Shared request model
# ===================================================================
class PreviewRequest(BaseModel):
    template_path: str
    template_format: str = "latex"
    mapping_json: str
    user_content: dict[str, str] = Field(default_factory=dict)
    figures: list[dict] = Field(default_factory=list)


class RenderResponse(BaseModel):
    pdf_base64: str | None = None
    tex_source: str | None = None
    error: str | None = None
    rendered: bool = False


# ===================================================================
# Preview endpoints
# ===================================================================
@router.post("/preview/text", response_model=dict)
async def preview_text(payload: PreviewRequest):
    """Return assembled LaTeX source for the preview panel."""
    mapping = TemplateMapping.model_validate_json(payload.mapping_json)
    from app.services.latex_assembler import assemble_latex
    text = assemble_latex(payload.template_path, mapping,
                          payload.user_content, figures=payload.figures)
    return {"assembled_text": text, "line_count": text.count("\n") + 1}


@router.post("/preview/render", response_model=RenderResponse)
async def preview_render(payload: PreviewRequest):
    """Compile LaTeX to PDF and return base64 for inline preview.

    Requires pdflatex in PATH. Falls back to returning the .tex source.
    """
    mapping = TemplateMapping.model_validate_json(payload.mapping_json)
    from app.services.latex_assembler import assemble_latex
    assembled = assemble_latex(payload.template_path, mapping,
                               payload.user_content, figures=payload.figures)

    # Try pdflatex compilation
    try:
        base64_pdf = _compile_to_base64(assembled, Path(payload.template_path).parent)
        if base64_pdf:
            return RenderResponse(pdf_base64=base64_pdf, rendered=True)
    except Exception:
        pass

    # Fallback: return source
    return RenderResponse(tex_source=assembled, rendered=False,
                          error="pdflatex 不可用，显示源码")


def _compile_to_base64(tex_source: str, resource_dir: Path) -> str | None:
    """Compile LaTeX to PDF and return as base64 string."""
    if not shutil.which("pdflatex"):
        return None

    tmpdir = Path(tempfile.mkdtemp())
    tex_path = tmpdir / "preview.tex"
    tex_path.write_text(tex_source, encoding="utf-8")

    # Copy template resources
    for ext in [".cls", ".sty", ".bst", ".bib"]:
        for f in resource_dir.glob(f"*{ext}"):
            shutil.copy2(f, tmpdir / f.name)
    fig_dir = resource_dir / "figures"
    if fig_dir.is_dir():
        shutil.copytree(fig_dir, tmpdir / "figures", dirs_exist_ok=True)
    # Also try Figures, images, pics
    for dn in ["Figures", "images", "pics", "fig"]:
        d = resource_dir / dn
        if d.is_dir():
            shutil.copytree(d, tmpdir / dn, dirs_exist_ok=True)

    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "preview.tex"],
                cwd=str(tmpdir), capture_output=True, text=True, timeout=60,
            )
        pdf_path = tmpdir / "preview.pdf"
        if pdf_path.exists():
            return base64.b64encode(pdf_path.read_bytes()).decode()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return None


# ===================================================================
# Export endpoints
# ===================================================================
@router.post("/export/tex")
async def export_tex(payload: PreviewRequest):
    mapping = TemplateMapping.model_validate_json(payload.mapping_json)
    from app.services.latex_assembler import assemble_latex
    text = assemble_latex(payload.template_path, mapping,
                          payload.user_content, figures=payload.figures)
    return PlainTextResponse(text, media_type="application/x-tex",
        headers={"Content-Disposition": "attachment; filename=paper_assembled.tex"})


@router.post("/export/pdf")
async def export_pdf(payload: PreviewRequest):
    mapping = TemplateMapping.model_validate_json(payload.mapping_json)
    from app.services.latex_assembler import assemble_latex
    assembled = assemble_latex(payload.template_path, mapping,
                               payload.user_content, figures=payload.figures)

    resource_dir = Path(payload.template_path).parent
    tmpdir = Path(tempfile.mkdtemp())
    tex_path = tmpdir / "paper.tex"
    tex_path.write_text(assembled, encoding="utf-8")

    for ext in [".cls", ".sty", ".bst", ".bib"]:
        for f in resource_dir.glob(f"*{ext}"):
            shutil.copy2(f, tmpdir / f.name)
    for dn in ["figures", "Figures", "images", "fig"]:
        d = resource_dir / dn
        if d.is_dir():
            shutil.copytree(d, tmpdir / dn, dirs_exist_ok=True)

    try:
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "paper.tex"],
                           cwd=str(tmpdir), capture_output=True, text=True, timeout=60)
        pdf = tmpdir / "paper.pdf"
        if pdf.exists():
            return FileResponse(pdf, media_type="application/pdf",
                                filename="paper_assembled.pdf")
    except Exception:
        pass

    return PlainTextResponse(assembled, media_type="application/x-tex",
        headers={"Content-Disposition": "attachment; filename=paper_assembled.tex"})


# ===================================================================
# Pipeline (async, background)
# ===================================================================
class PipelineRequest(BaseModel):
    journal_name: str = Field(...)
    template_format: str = Field(default="latex")
    template_path: str = Field(default="")
    user_content: dict[str, str] = Field(default_factory=dict)
    figures: list[dict] = Field(default_factory=list)
    user_config_id: str | None = None


class PipelineResponse(BaseModel):
    task_id: str; status: str; agent_log: list[str]; template_path: str
    mapping_json: str | None; parse_used_llm: bool
    rag_constraints: list[dict]; assembled_text: str | None
    output_path: str | None; error: str | None


_pipelines: dict[str, dict] = {}


@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(payload: PipelineRequest, db: AsyncSession = Depends(get_db)):
    import asyncio
    tid = uuid.uuid4().hex[:12]
    llm_config = None
    if payload.user_config_id:
        from uuid import UUID
        from app.services.user_config_service import get_user_config_with_llm_configs
        user = await get_user_config_with_llm_configs(db, UUID(payload.user_config_id))
        if user and user.llm_configs:
            active = [c for c in user.llm_configs if c.is_active]
            if active:
                c = active[0]
                llm_config = {"provider": c.provider, "api_key": c.api_key_encrypted or "",
                              "base_url": c.base_url or "", "model_name": c.model_name or ""}

    async def _run():
        from app.agents.supervisor import run_pipeline as run
        try:
            result = await run(journal_name=payload.journal_name, template_format=payload.template_format,
                               template_path=payload.template_path, user_content=payload.user_content,
                               figures=payload.figures, llm_config=llm_config)
            _pipelines[tid] = dict(result)
        except Exception as exc:
            _pipelines[tid] = {"status": "failed", "error": str(exc), "agent_log": []}

    asyncio.create_task(_run())
    return PipelineResponse(task_id=tid, status="running", agent_log=["已启动"],
                            template_path="", mapping_json=None, parse_used_llm=False,
                            rag_constraints=[], assembled_text=None, output_path=None, error=None)


@router.get("/pipeline/status", response_model=PipelineResponse)
async def pipeline_status(task_id: str = Query(...)):
    d = _pipelines.get(task_id)
    if not d:
        raise HTTPException(404, "任务未找到")
    return PipelineResponse(task_id=task_id, status=d.get("status", ""),
                            agent_log=d.get("agent_log", []),
                            template_path=d.get("template_path", ""),
                            mapping_json=d.get("mapping_json"),
                            parse_used_llm=d.get("parse_used_llm", False),
                            rag_constraints=d.get("rag_constraints", []),
                            assembled_text=d.get("assembled_text"),
                            output_path=d.get("output_path"), error=d.get("error"))
