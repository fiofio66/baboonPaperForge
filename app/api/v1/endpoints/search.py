"""
Search Agent API endpoint.

POST /api/v1/search/start
  - Accepts journal_name + template_format
  - Creates a TaskRecord
  - Runs the search workflow in the background
  - Returns task_id for polling via GET /api/v1/tasks/{id}
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.search_workflow import run_search
from app.db.session import get_db
from app.services import task_service, template_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


class SearchStartRequest(BaseModel):
    journal_name: str = Field(..., max_length=256, examples=["IEEE Internet of Things Journal"])
    template_format: str = Field(default="latex", max_length=16, examples=["latex"])
    user_config_id: str | None = Field(None, examples=["550e8400-..."])


class SearchStartResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/start", response_model=SearchStartResponse)
async def start_search(
    payload: SearchStartRequest, db: AsyncSession = Depends(get_db)
):
    """Kick off a template search workflow.

    Creates a TaskRecord and runs the search in the background.
    Poll ``GET /api/v1/tasks/{task_id}`` for results.
    """
    # Create a task record
    from uuid import UUID

    user_id = UUID(payload.user_config_id) if payload.user_config_id else None
    task = await task_service.create_task(
        db,
        journal_name=payload.journal_name,
        template_format=payload.template_format,
        user_config_id=user_id,
    )
    await task_service.transition_task_status(db, task, "searching")
    task_id = str(task.id)

    # Run search in background (don't await — let it complete async)
    async def _bg_search():
        try:
            result = await run_search(
                journal_name=payload.journal_name,
                template_format=payload.template_format,
            )

            from app.db.session import async_session_factory
            async with async_session_factory() as bg_db:
                bg_task = await task_service.get_task(bg_db, task.id)
                if bg_task is None:
                    return

                if result.get("status") == "done":
                    # Create TemplateMetadata from result
                    tmpl = await template_service.create_template(
                        bg_db,
                        journal_name=payload.journal_name,
                        template_format=payload.template_format,
                        download_path=result.get("extract_dir", ""),
                    )
                    await task_service.update_task(
                        bg_db, bg_task,
                        template_metadata_id=tmpl.id,
                    )
                    await task_service.transition_task_status(bg_db, bg_task, "completed")
                else:
                    await task_service.transition_task_status(
                        bg_db, bg_task, "failed",
                        error_message=result.get("error", "Unknown error"),
                    )
        except Exception as exc:
            logger.exception("Background search failed")
            try:
                from app.db.session import async_session_factory
                async with async_session_factory() as bg_db:
                    bg_task = await task_service.get_task(bg_db, task.id)
                    if bg_task:
                        await task_service.transition_task_status(
                            bg_db, bg_task, "failed", error_message=str(exc)
                        )
            except Exception:
                logger.exception("Failed to update task status")

    asyncio.create_task(_bg_search())

    return SearchStartResponse(
        task_id=task_id,
        status="searching",
        message=f"Search started for '{payload.journal_name}'. Poll /tasks/{task_id} for status.",
    )
