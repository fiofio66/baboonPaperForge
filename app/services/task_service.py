"""
Task lifecycle service.

Manages the full workflow: pending → searching → analyzing →
awaiting_input → assembling → completed / failed.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_record import TaskRecord
from app.services.base import create_instance, get_by_id, update_instance


async def get_task(session: AsyncSession, task_id: UUID) -> TaskRecord | None:
    return await get_by_id(session, TaskRecord, task_id)  # type: ignore[return-value]


async def list_tasks(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    user_config_id: UUID | None = None,
) -> list[TaskRecord]:
    stmt = select(TaskRecord).offset(skip).limit(limit)
    if status is not None:
        stmt = stmt.where(TaskRecord.status == status)
    if user_config_id is not None:
        stmt = stmt.where(TaskRecord.user_config_id == user_config_id)
    stmt = stmt.order_by(TaskRecord.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_task(
    session: AsyncSession,
    journal_name: str,
    template_format: str,
    user_config_id: UUID | None = None,
) -> TaskRecord:
    return await create_instance(  # type: ignore[return-value]
        session,
        TaskRecord,
        journal_name=journal_name,
        template_format=template_format,
        user_config_id=user_config_id,
    )


async def update_task(
    session: AsyncSession, task: TaskRecord, **kwargs
) -> TaskRecord:
    return await update_instance(session, task, **kwargs)  # type: ignore[return-value]


async def transition_task_status(
    session: AsyncSession, task: TaskRecord, new_status: str, *, error_message: str | None = None
) -> TaskRecord:
    """Atomically transition a task to a new status with optional error detail."""
    from datetime import datetime, timezone

    task.status = new_status
    if error_message is not None:
        task.error_message = error_message
    if new_status in ("completed", "failed"):
        task.completed_at = datetime.now(timezone.utc)
    await session.flush()
    return task
