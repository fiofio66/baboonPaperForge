"""
API v1 router — aggregates all v1 sub-routers.

Current endpoints:
- GET  /api/v1/health   → health check (DB + overall status)
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["v1"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Lightweight health check.
    Returns the application name and status.
    DB connectivity will be added in a subsequent iteration.
    """
    return {"status": "ok", "app": "baboonPaperForge"}


@router.get("/health/db")
async def health_check_db() -> dict[str, str | bool]:
    """
    Deep health check — verifies PostgreSQL connectivity via asyncpg.
    """
    from sqlalchemy import text

    from app.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": True}
    except Exception as exc:
        return {"status": "error", "database": False, "detail": str(exc)}
