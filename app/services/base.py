"""
Generic async CRUD helpers.

All functions receive an AsyncSession as their first argument so they can
be used directly inside FastAPI endpoints that depend on get_db().
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


async def get_by_id(
    session: AsyncSession, model: type[Base], obj_id: UUID
) -> Base | None:
    """Fetch a single row by primary key (UUID)."""
    return await session.get(model, obj_id)


async def get_all(
    session: AsyncSession,
    model: type[Base],
    *,
    skip: int = 0,
    limit: int = 100,
    order_by: Any = None,
) -> list[Base]:
    """Return a page of results ordered by the given column (defaults to PK)."""
    stmt = select(model).offset(skip).limit(limit)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_instance(
    session: AsyncSession, model: type[Base], **kwargs: Any
) -> Base:
    """Create a new row and flush so the PK is available."""
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()
    return instance


async def update_instance(
    session: AsyncSession, instance: Base, **kwargs: Any
) -> Base:
    """Patch an existing instance with the given keyword fields (non-None only)."""
    for key, value in kwargs.items():
        if value is not None:
            setattr(instance, key, value)
    await session.flush()
    return instance


async def delete_instance(session: AsyncSession, instance: Base) -> None:
    """Delete a row."""
    await session.delete(instance)
    await session.flush()
