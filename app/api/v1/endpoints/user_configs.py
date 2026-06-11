"""
User config & LLM config endpoints.

POST   /api/v1/users                              — create user (idempotent)
GET    /api/v1/users/{id}                         — get user + masked LLM configs
PATCH  /api/v1/users/{id}                         — update user
POST   /api/v1/users/{id}/llm-configs             — add LLM config (encrypts key)
GET    /api/v1/users/{id}/llm-configs             — list LLM configs (keys masked)
PATCH  /api/v1/users/{id}/llm-configs/{config_id} — update LLM config
DELETE /api/v1/users/{id}/llm-configs/{config_id} — delete LLM config
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user_config import (
    LLMConfigCreate,
    LLMConfigRead,
    LLMConfigUpdate,
    UserConfigCreate,
    UserConfigRead,
    UserConfigUpdate,
    UserConfigWithLLMs,
)
from app.services import user_config_service

router = APIRouter(prefix="/users", tags=["users"])


# ======================================================================
# UserConfig
# ======================================================================

@router.post("", response_model=UserConfigRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserConfigCreate, db: AsyncSession = Depends(get_db)):
    """Create or return existing user config (idempotent by user_identifier)."""
    user = await user_config_service.create_user_config(
        db,
        user_identifier=payload.user_identifier,
        default_provider=payload.default_provider,
    )
    return user


@router.get("/{user_id}", response_model=UserConfigWithLLMs)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await user_config_service.get_user_config_with_llm_configs(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserConfigRead)
async def update_user(
    user_id: UUID, payload: UserConfigUpdate, db: AsyncSession = Depends(get_db)
):
    user = await user_config_service.get_user_config(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_config_service.update_user_config(
        db, user, **payload.model_dump(exclude_unset=True)
    )


# ======================================================================
# LLMConfig
# ======================================================================

@router.post(
    "/{user_id}/llm-configs",
    response_model=LLMConfigRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_llm_config(
    user_id: UUID, payload: LLMConfigCreate, db: AsyncSession = Depends(get_db)
):
    # Verify user exists
    user = await user_config_service.get_user_config(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_config_service.add_llm_config(
        db,
        user_config_id=user_id,
        provider=payload.provider,
        api_key=payload.api_key,
        base_url=payload.base_url,
        model_name=payload.model_name,
        is_active=payload.is_active,
    )


@router.get("/{user_id}/llm-configs", response_model=list[LLMConfigRead])
async def list_llm_configs(
    user_id: UUID, db: AsyncSession = Depends(get_db)
):
    user = await user_config_service.get_user_config(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_config_service.list_llm_configs(db, user_id)


@router.patch("/{user_id}/llm-configs/{config_id}", response_model=LLMConfigRead)
async def update_llm_config(
    user_id: UUID,
    config_id: UUID,
    payload: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    config = await user_config_service.get_llm_config(db, config_id)
    if config is None or config.user_config_id != user_id:
        raise HTTPException(status_code=404, detail="LLM config not found")
    return await user_config_service.update_llm_config(
        db, config, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{user_id}/llm-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    user_id: UUID, config_id: UUID, db: AsyncSession = Depends(get_db)
):
    config = await user_config_service.get_llm_config(db, config_id)
    if config is None or config.user_config_id != user_id:
        raise HTTPException(status_code=404, detail="LLM config not found")
    await user_config_service.delete_llm_config(db, config)
    return None
