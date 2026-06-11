"""
API v1 router — aggregates all v1 sub-routers.

Endpoints:
- GET    /api/v1/health                     → shallow health check
- GET    /api/v1/health/db                  → deep health check (DB ping)
- CRUD   /api/v1/templates                  → template metadata
- CRUD   /api/v1/users + /llm-configs       → user config + BYOK LLM keys
- CRUD   /api/v1/tasks                      → task lifecycle
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import assembler, files, parser, pipeline, rag, search, tasks, templates, user_configs
from app.db.session import get_db

router = APIRouter(prefix="", tags=["v1"])

# ---------------------------------------------------------------------------
# Sub-routers
# ---------------------------------------------------------------------------
router.include_router(templates.router)
router.include_router(user_configs.router)
router.include_router(tasks.router)
router.include_router(parser.router)
router.include_router(assembler.router)
router.include_router(search.router)
router.include_router(rag.router)
router.include_router(pipeline.router)
router.include_router(files.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Lightweight health check.
    Returns the application name and status.
    """
    return {"status": "ok", "app": "baboonPaperForge"}


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)) -> dict[str, str | bool]:
    """
    Deep health check — verifies database connectivity via the active session.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": True}
    except Exception as exc:
        return {"status": "error", "database": False, "detail": str(exc)}
