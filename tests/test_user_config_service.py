"""
Test user config & LLM config service — with encryption verification.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt
from app.services.user_config_service import (
    add_llm_config,
    create_user_config,
    get_active_llm_config,
    get_llm_config,
    get_user_config_with_llm_configs,
    list_llm_configs,
    update_llm_config,
)


# ---------------------------------------------------------------------------
# Service layer tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_user_config(db_session: AsyncSession):
    user = await create_user_config(db_session, "alice", "anthropic")
    assert user.id is not None
    assert user.user_identifier == "alice"
    assert user.default_provider == "anthropic"


@pytest.mark.asyncio
async def test_create_user_config_idempotent(db_session: AsyncSession):
    a = await create_user_config(db_session, "bob")
    b = await create_user_config(db_session, "bob")
    assert a.id == b.id


@pytest.mark.asyncio
async def test_add_llm_config_encrypts_key(db_session: AsyncSession):
    user = await create_user_config(db_session, "charlie")
    cfg = await add_llm_config(
        db_session,
        user_config_id=user.id,
        provider="openai",
        api_key="sk-secret-abc123",
        model_name="gpt-4o",
    )

    # Ciphertext stored, NOT plaintext
    assert cfg.api_key_encrypted != "sk-secret-abc123"
    assert cfg.api_key_encrypted is not None

    # Decrypt recovers original
    assert decrypt(cfg.api_key_encrypted) == "sk-secret-abc123"


@pytest.mark.asyncio
async def test_add_llm_config_ollama_no_key(db_session: AsyncSession):
    user = await create_user_config(db_session, "dave")
    cfg = await add_llm_config(
        db_session,
        user_config_id=user.id,
        provider="ollama",
        api_key=None,
        base_url="http://localhost:11434",
    )
    assert cfg.api_key_encrypted is None


@pytest.mark.asyncio
async def test_list_llm_configs(db_session: AsyncSession):
    user = await create_user_config(db_session, "eve")
    await add_llm_config(db_session, user.id, "openai", api_key="sk-1")
    await add_llm_config(db_session, user.id, "anthropic", api_key="sk-2")
    cfgs = await list_llm_configs(db_session, user.id)
    assert len(cfgs) == 2


@pytest.mark.asyncio
async def test_update_llm_config_re_encrypts(db_session: AsyncSession):
    user = await create_user_config(db_session, "frank")
    cfg = await add_llm_config(db_session, user.id, "openai", api_key="sk-old")

    old_cipher = cfg.api_key_encrypted
    updated = await update_llm_config(db_session, cfg, api_key="sk-new")
    new_cipher = updated.api_key_encrypted

    assert new_cipher != old_cipher
    assert decrypt(new_cipher) == "sk-new"


@pytest.mark.asyncio
async def test_get_active_llm_config(db_session: AsyncSession):
    user = await create_user_config(db_session, "grace")
    await add_llm_config(db_session, user.id, "openai", api_key="sk-active", is_active=True)
    await add_llm_config(db_session, user.id, "gemini", api_key="sk-other", is_active=False)

    active = await get_active_llm_config(db_session, user.id, "openai")
    assert active is not None
    assert active.provider == "openai"

    inactive = await get_active_llm_config(db_session, user.id, "gemini")
    assert inactive is None  # is_active=False


@pytest.mark.asyncio
async def test_get_user_with_llm_configs(db_session: AsyncSession):
    user = await create_user_config(db_session, "heidi")
    await add_llm_config(db_session, user.id, "openai", api_key="sk-x")
    await add_llm_config(db_session, user.id, "anthropic", api_key="sk-y")

    full = await get_user_config_with_llm_configs(db_session, user.id)
    assert full is not None
    assert len(full.llm_configs) == 2
    # Verify eager-loaded children are LLMConfig instances
    assert full.llm_configs[0].provider in ("openai", "anthropic")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_key_masked_on_read(async_client, db_session):
    """API responses must NEVER expose the plaintext or ciphertext API key."""
    user = await create_user_config(db_session, "mask-test")
    await add_llm_config(db_session, user.id, "openai", api_key="sk-ultra-secret")

    resp = await async_client.get(f"/api/v1/users/{user.id}")
    assert resp.status_code == 200
    data = resp.json()

    llm_cfg = data["llm_configs"][0]
    key_field = llm_cfg.get("api_key_encrypted")
    # Must be masked — NOT the ciphertext > 10 chars
    assert key_field is None or key_field == "********" or len(key_field) <= 8


@pytest.mark.asyncio
async def test_create_user_api(async_client):
    resp = await async_client.post(
        "/api/v1/users",
        json={"user_identifier": "api-user", "default_provider": "openai"},
    )
    assert resp.status_code == 201
    assert resp.json()["user_identifier"] == "api-user"


@pytest.mark.asyncio
async def test_add_llm_config_api(async_client, db_session):
    user = await create_user_config(db_session, "llm-user")
    resp = await async_client.post(
        f"/api/v1/users/{user.id}/llm-configs",
        json={
            "provider": "anthropic",
            "api_key": "sk-api-test-key",
            "model_name": "claude-opus-4-8",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    # Response must mask the key
    assert data["api_key_encrypted"] == "********"
    # But provider and model are visible
    assert data["provider"] == "anthropic"
    assert data["model_name"] == "claude-opus-4-8"


@pytest.mark.asyncio
async def test_nonexistent_user_returns_404(async_client):
    from uuid import uuid4

    resp = await async_client.get(f"/api/v1/users/{uuid4()}")
    assert resp.status_code == 404
