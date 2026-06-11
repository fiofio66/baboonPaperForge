"""
Test the health-check endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "baboonPaperForge"


@pytest.mark.asyncio
async def test_health_check_db(async_client, async_engine):
    """Deep health check — should succeed against the test SQLite DB."""
    resp = await async_client.get("/api/v1/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] is True
