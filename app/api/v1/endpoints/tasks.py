"""
Task record endpoints.

POST  /api/v1/tasks       — create a task
GET   /api/v1/tasks       — list tasks (filterable by status, user)
GET   /api/v1/tasks/{id}  — get task detail
PATCH /api/v1/tasks/{id}  — update task (status transitions, attach results)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = Query(None, alias="status"),
    user_config_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.list_tasks(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        user_config_id=user_config_id,
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    return await task_service.create_task(
        db,
        journal_name=payload.journal_name,
        template_format=payload.template_format,
        user_config_id=payload.user_config_id,
    )


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID, payload: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    task = await task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return await task_service.update_task(
        db, task, **payload.model_dump(exclude_unset=True)
    )
