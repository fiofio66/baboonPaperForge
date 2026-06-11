"""
Template metadata service — thin wrappers over generic CRUD with
domain-specific validation.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import TemplateMetadata
from app.services.base import (
    create_instance,
    delete_instance,
    get_all,
    get_by_id,
    update_instance,
)


async def get_template(session: AsyncSession, template_id: UUID) -> TemplateMetadata | None:
    return await get_by_id(session, TemplateMetadata, template_id)  # type: ignore[return-value]


async def list_templates(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[TemplateMetadata]:
    return await get_all(session, TemplateMetadata, skip=skip, limit=limit)  # type: ignore[return-value]


async def create_template(session: AsyncSession, **kwargs) -> TemplateMetadata:
    return await create_instance(session, TemplateMetadata, **kwargs)  # type: ignore[return-value]


async def update_template(session: AsyncSession, template: TemplateMetadata, **kwargs) -> TemplateMetadata:
    return await update_instance(session, template, **kwargs)  # type: ignore[return-value]


async def delete_template(session: AsyncSession, template: TemplateMetadata) -> None:
    await delete_instance(session, template)
