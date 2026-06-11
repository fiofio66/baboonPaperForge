"""
Zero-Token Assembler — unified entry point.

Dispatches to LaTeX or Word assembler based on template format.
Reads the stored TemplateMetadata + Mapping JSON, injects user content,
and writes the output file.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.assemble import AssembleResponse, FigureConfig
from app.schemas.mapping import TemplateMapping
from app.services.docx_assembler import assemble_docx, save_assembled_docx
from app.services.latex_assembler import assemble_latex, save_assembled_latex
from app.services.template_service import get_template, update_template


async def assemble_template(
    template_id: UUID,
    user_content: dict[str, str],
    figures: list[FigureConfig] | None,
    db: AsyncSession,
) -> AssembleResponse:
    """Run the full assembly pipeline.

    1. Fetch TemplateMetadata from DB
    2. Parse its stored mapping_json
    3. Dispatch to LaTeX or Word assembler
    4. Save output to workdir
    5. Update the template record with the output path
    """
    tmpl = await get_template(db, template_id)
    if tmpl is None:
        raise ValueError(f"Template not found: {template_id}")

    # Parse stored mapping
    if not tmpl.mapping_json:
        raise ValueError("Template has no mapping_json — run the parser first.")
    mapping = TemplateMapping.model_validate_json(tmpl.mapping_json)

    # Ensure the template file exists
    template_path = Path(tmpl.download_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Template file missing: {template_path}")

    figures = figures or []

    # Dispatch
    fmt = mapping.format.lower()
    workdir = Path(settings.TEMPLATE_WORKDIR).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if fmt in ("latex", "tex"):
        assembled_text = assemble_latex(
            template_path, mapping, user_content,
            figures=[f.model_dump() for f in figures],
        )
        out_name = f"{template_path.stem}_assembled.tex"
        output_path = workdir / out_name
        save_assembled_latex(assembled_text, output_path)

    elif fmt in ("docx", "word", "doc"):
        doc = assemble_docx(template_path, mapping, user_content)
        out_name = f"{template_path.stem}_assembled.docx"
        output_path = workdir / out_name
        save_assembled_docx(doc, output_path)

    else:
        raise ValueError(f"Unsupported format: {fmt}")

    # Update DB with output path
    filled_count = sum(1 for v in user_content.values() if v.strip())
    await update_template(
        db, tmpl, download_path=str(output_path)
    )

    return AssembleResponse(
        status="ok",
        template_id=str(template_id),
        output_path=str(output_path.resolve()),
        output_format=fmt,
        module_count=len(mapping.modules),
        filled_count=filled_count,
    )
