"""
Search Agent API endpoints.

GET  /api/v1/search/suggest?q=iotj  → suggestions list (instant)
POST /api/v1/search/start            → download best match
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.search_service import list_all_journals, llm_resolve_query, match_all, search_template_links
from app.services import task_service, template_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/suggest")
async def suggest_journals(q: str = Query(..., min_length=1, description="Partial journal name or abbreviation")):
    """Get matching journal suggestions as you type.

    Returns a list of {id, name, match_count}.
    First tries exact alias match. Falls back to LLM resolution if nothing found.
    """
    # 1. Direct match against alias DB
    results = match_all(q)
    if results:
        return [
            {"id": r["id"], "name": r["name"], "match": "direct"}
            for r in results[:8]
        ]

    # 2. No direct match — return empty, frontend shows "try full name"
    return []


@router.get("/journals")
async def list_journals():
    """List all known journal templates for browsing."""
    return list_all_journals()


# ---------------------------------------------------------------------------
# Search + download (with optional LLM resolve)
# ---------------------------------------------------------------------------
class SearchStartRequest(BaseModel):
    journal_name: str = Field(..., max_length=256, examples=["iotj"])
    template_format: str = Field(default="latex", max_length=16, examples=["latex"])
    user_config_id: str | None = Field(None)
    use_llm_resolve: bool = Field(True, description="Use LLM to resolve abbreviations")


class SearchStartResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/start", response_model=SearchStartResponse)
async def start_search(payload: SearchStartRequest, db: AsyncSession = Depends(get_db)):
    """Search & download a template. Optionally uses LLM to resolve abbreviations."""
    journal_name = payload.journal_name

    # If LLM resolve is enabled and not a direct match
    if payload.use_llm_resolve and not match_all(journal_name):
        llm_config = None
        if payload.user_config_id:
            from app.services.user_config_service import get_user_config_with_llm_configs
            import uuid
            try:
                uid = uuid.UUID(payload.user_config_id)
                user = await get_user_config_with_llm_configs(db, uid)
                if user and user.llm_configs:
                    active = [c for c in user.llm_configs if c.is_active]
                    if active:
                        cfg = active[0]
                        llm_config = {
                            "provider": cfg.provider,
                            "api_key": cfg.api_key_encrypted or "",
                            "base_url": cfg.base_url or "",
                            "model_name": cfg.model_name or "",
                        }
            except Exception:
                pass

        resolved = await llm_resolve_query(journal_name, llm_config)
        if resolved and resolved != journal_name:
            journal_name = resolved
            # Re-check match_all with resolved name
            direct = match_all(journal_name)
            if not direct:
                # Still no match, just use the resolved name as-is
                pass

    # Create task and run search in background
    user_id = UUID(payload.user_config_id) if payload.user_config_id else None
    task = await task_service.create_task(
        db, journal_name=journal_name, template_format=payload.template_format, user_config_id=user_id
    )
    await task_service.transition_task_status(db, task, "searching")
    task_id_str = str(task.id)

    async def _bg_search():
        try:
            from app.services.downloader import download_and_extract
            results = search_template_links(journal_name, payload.template_format)
            if not results:
                from app.db.session import async_session_factory
                async with async_session_factory() as bg_db:
                    bg_task = await task_service.get_task(bg_db, task.id)
                    if bg_task:
                        await task_service.transition_task_status(
                            bg_db, bg_task, "failed", error_message="No template found for this journal"
                        )
                return

            best = results[0]
            try:
                dl_result = await download_and_extract(best["url"], journal_name, payload.template_format)
                from app.db.session import async_session_factory
                async with async_session_factory() as bg_db:
                    bg_task = await task_service.get_task(bg_db, task.id)
                    if bg_task:
                        tmpl = await template_service.create_template(
                            bg_db,
                            journal_name=journal_name,
                            template_format=payload.template_format,
                            download_path=dl_result["extract_dir"],
                        )
                        await task_service.update_task(bg_db, bg_task, template_metadata_id=tmpl.id)
                        await task_service.transition_task_status(bg_db, bg_task, "completed")
            except Exception as dl_err:
                from app.db.session import async_session_factory
                async with async_session_factory() as bg_db:
                    bg_task = await task_service.get_task(bg_db, task.id)
                    if bg_task:
                        await task_service.transition_task_status(
                            bg_db, bg_task, "failed", error_message=str(dl_err)
                        )
        except Exception as exc:
            logger.exception("Background search failed")
            try:
                from app.db.session import async_session_factory
                async with async_session_factory() as bg_db:
                    bg_task = await task_service.get_task(bg_db, task.id)
                    if bg_task:
                        await task_service.transition_task_status(bg_db, bg_task, "failed", error_message=str(exc))
            except Exception:
                pass

    asyncio.create_task(_bg_search())

    return SearchStartResponse(
        task_id=task_id_str, status="searching",
        message=f"Searching template for '{journal_name}'. Poll /tasks/{task_id_str} for status."
    )
