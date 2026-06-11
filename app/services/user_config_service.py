"""
User config & LLM config service.

Encrypts API keys via Fernet before persistence; masks them on read.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decrypt, encrypt
from app.models.user_config import LLMConfig, UserConfig
from app.services.base import (
    create_instance,
    delete_instance,
    get_all,
    get_by_id,
    update_instance,
)


# ======================================================================
# UserConfig
# ======================================================================

async def get_user_config(
    session: AsyncSession, user_config_id: UUID
) -> UserConfig | None:
    return await get_by_id(session, UserConfig, user_config_id)  # type: ignore[return-value]


async def get_user_config_by_identifier(
    session: AsyncSession, user_identifier: str
) -> UserConfig | None:
    stmt = select(UserConfig).where(UserConfig.user_identifier == user_identifier)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_user_configs(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[UserConfig]:
    return await get_all(session, UserConfig, skip=skip, limit=limit)  # type: ignore[return-value]


async def create_user_config(
    session: AsyncSession, user_identifier: str, default_provider: str = "openai"
) -> UserConfig:
    """Idempotent create — returns existing if already present."""
    existing = await get_user_config_by_identifier(session, user_identifier)
    if existing is not None:
        return existing
    return await create_instance(  # type: ignore[return-value]
        session, UserConfig, user_identifier=user_identifier, default_provider=default_provider
    )


async def update_user_config(
    session: AsyncSession, user_config: UserConfig, **kwargs
) -> UserConfig:
    return await update_instance(session, user_config, **kwargs)  # type: ignore[return-value]


async def delete_user_config(session: AsyncSession, user_config: UserConfig) -> None:
    await delete_instance(session, user_config)


# ======================================================================
# LLMConfig
# ======================================================================

async def get_llm_config(
    session: AsyncSession, llm_config_id: UUID
) -> LLMConfig | None:
    return await get_by_id(session, LLMConfig, llm_config_id)  # type: ignore[return-value]


async def list_llm_configs(
    session: AsyncSession, user_config_id: UUID
) -> list[LLMConfig]:
    stmt = (
        select(LLMConfig)
        .where(LLMConfig.user_config_id == user_config_id)
        .order_by(LLMConfig.provider)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def add_llm_config(
    session: AsyncSession,
    user_config_id: UUID,
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    is_active: bool = True,
) -> LLMConfig:
    """Create an LLMConfig. Encrypts `api_key` before storage."""
    encrypted = encrypt(api_key) if api_key else None
    return await create_instance(  # type: ignore[return-value]
        session,
        LLMConfig,
        user_config_id=user_config_id,
        provider=provider,
        api_key_encrypted=encrypted,
        base_url=base_url,
        model_name=model_name,
        is_active=is_active,
    )


async def update_llm_config(
    session: AsyncSession,
    llm_config: LLMConfig,
    *,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    is_active: bool | None = None,
) -> LLMConfig:
    """Patch an LLMConfig. Re-encrypts if a new `api_key` is provided."""
    if api_key is not None:
        llm_config.api_key_encrypted = encrypt(api_key)
    if provider is not None:
        llm_config.provider = provider
    if base_url is not None:
        llm_config.base_url = base_url
    if model_name is not None:
        llm_config.model_name = model_name
    if is_active is not None:
        llm_config.is_active = is_active
    await session.flush()
    return llm_config


async def delete_llm_config(
    session: AsyncSession, llm_config: LLMConfig
) -> None:
    await delete_instance(session, llm_config)


async def get_active_llm_config(
    session: AsyncSession, user_config_id: UUID, provider: str
) -> LLMConfig | None:
    """Return the active LLMConfig for a given user + provider (for LLM factory)."""
    stmt = (
        select(LLMConfig)
        .where(
            LLMConfig.user_config_id == user_config_id,
            LLMConfig.provider == provider,
            LLMConfig.is_active.is_(True),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_config_with_llm_configs(
    session: AsyncSession, user_config_id: UUID
) -> UserConfig | None:
    """Fetch UserConfig with its LLMConfig children eagerly loaded."""
    stmt = (
        select(UserConfig)
        .where(UserConfig.id == user_config_id)
        .options(selectinload(UserConfig.llm_configs))
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()
