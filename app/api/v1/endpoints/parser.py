"""
Template analysis endpoint.

POST /api/v1/parser/analyze
  - Accepts a template_id (already stored in DB).
  - Runs the parser on the template file.
  - Saves the resulting mapping JSON back to TemplateMetadata.
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.mapping import TemplateMapping
from app.services import template_parser, template_service

router = APIRouter(prefix="/parser", tags=["parser"])


@router.post("/analyze", response_model=TemplateMapping)
async def analyze_template(
    template_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Analyze a stored template by ID.
    Parses its .tex/.docx file and returns the module structure tree.
    Persists the mapping JSON to the database.
    """
    tmpl = await template_service.get_template(db, template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        mapping = template_parser.parse_template(
            tmpl.download_path, tmpl.template_format
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail=f"Template file not found at: {tmpl.download_path}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Persist mapping JSON to DB
    mapping_json = mapping.model_dump_json(indent=2)
    await template_service.update_template(db, tmpl, mapping_json=mapping_json)

    return mapping
