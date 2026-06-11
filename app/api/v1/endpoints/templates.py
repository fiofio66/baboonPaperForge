"""
Template metadata CRUD endpoints.

GET    /api/v1/templates          — list templates
GET    /api/v1/templates/{id}     — get one template
POST   /api/v1/templates          — create template
PATCH  /api/v1/templates/{id}     — update template
DELETE /api/v1/templates/{id}     — delete template
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate
from app.services import template_service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateRead])
async def list_templates(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    return await template_service.list_templates(db, skip=skip, limit=limit)


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: UUID, db: AsyncSession = Depends(get_db)
):
    tmpl = await template_service.get_template(db, template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate, db: AsyncSession = Depends(get_db)
):
    return await template_service.create_template(db, **payload.model_dump())


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    tmpl = await template_service.get_template(db, template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return await template_service.update_template(
        db, tmpl, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID, db: AsyncSession = Depends(get_db)
):
    tmpl = await template_service.get_template(db, template_id)
    if tmpl is None:
        raise HTTPException(status_code=404, detail="Template not found")
    await template_service.delete_template(db, tmpl)
    return None
