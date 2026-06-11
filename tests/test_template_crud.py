"""
Test template CRUD (service layer + API endpoints).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.template_service import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    update_template,
)


@pytest.mark.asyncio
async def test_create_template(db_session: AsyncSession):
    tmpl = await create_template(
        db_session,
        journal_name="IEEE IoT Journal",
        template_format="latex",
        download_path="/tmp/ieee_iot",
    )
    assert tmpl.id is not None
    assert tmpl.journal_name == "IEEE IoT Journal"
    assert tmpl.template_format == "latex"


@pytest.mark.asyncio
async def test_get_template(db_session: AsyncSession):
    tmpl = await create_template(
        db_session,
        journal_name="Test Journal",
        template_format="docx",
        download_path="/tmp/test",
    )
    fetched = await get_template(db_session, tmpl.id)
    assert fetched is not None
    assert fetched.id == tmpl.id


@pytest.mark.asyncio
async def test_list_templates(db_session: AsyncSession):
    await create_template(db_session, journal_name="A", template_format="latex", download_path="/a")
    await create_template(db_session, journal_name="B", template_format="docx", download_path="/b")
    results = await list_templates(db_session, skip=0, limit=10)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_update_template(db_session: AsyncSession):
    tmpl = await create_template(
        db_session, journal_name="Old Name", template_format="latex", download_path="/old"
    )
    updated = await update_template(db_session, tmpl, journal_name="New Name")
    assert updated.journal_name == "New Name"


@pytest.mark.asyncio
async def test_delete_template(db_session: AsyncSession):
    tmpl = await create_template(
        db_session, journal_name="To Delete", template_format="latex", download_path="/del"
    )
    await delete_template(db_session, tmpl)
    gone = await get_template(db_session, tmpl.id)
    assert gone is None


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_templates_api(async_client, db_session):
    # Seed data via service
    await create_template(db_session, journal_name="API Journal", template_format="latex", download_path="/api")
    resp = await async_client.get("/api/v1/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["journal_name"] == "API Journal"


@pytest.mark.asyncio
async def test_get_template_api(async_client, db_session):
    tmpl = await create_template(db_session, journal_name="Single", template_format="docx", download_path="/single")
    resp = await async_client.get(f"/api/v1/templates/{tmpl.id}")
    assert resp.status_code == 200
    assert resp.json()["journal_name"] == "Single"


@pytest.mark.asyncio
async def test_create_template_api(async_client):
    resp = await async_client.post(
        "/api/v1/templates",
        json={
            "journal_name": "Created via API",
            "template_format": "latex",
            "download_path": "/created",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["journal_name"] == "Created via API"


@pytest.mark.asyncio
async def test_delete_template_api(async_client, db_session):
    tmpl = await create_template(db_session, journal_name="API Del", template_format="latex", download_path="/api_del")
    resp = await async_client.delete(f"/api/v1/templates/{tmpl.id}")
    assert resp.status_code == 204
    # Verify it's gone
    resp2 = await async_client.get(f"/api/v1/templates/{tmpl.id}")
    assert resp2.status_code == 404
