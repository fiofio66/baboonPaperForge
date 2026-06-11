"""
Zero-Token Assembler endpoint.

POST /api/v1/assembler/assemble
  - Accepts template_id + user_content (dict of module_id → text) + figures
  - Runs the assembler (NO LLM INVOLVED)
  - Returns the output file path
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.assemble import AssembleRequest, AssembleResponse
from app.services.assembler import assemble_template

router = APIRouter(prefix="/assembler", tags=["assembler"])


@router.post("/assemble", response_model=AssembleResponse)
async def assemble(
    payload: AssembleRequest, db: AsyncSession = Depends(get_db)
):
    """
    Zero-token content injection.

    Takes a parsed template (with mapping_json) and user content for each
    module, then injects content directly via regex/environment replacement.
    No LLM is called — pure Python string processing.
    """
    try:
        template_id = UUID(payload.template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template_id UUID")

    try:
        result = await assemble_template(
            template_id=template_id,
            user_content=payload.user_content,
            figures=payload.figures,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
