"""
模板搜索与下载 API

GET  /api/v1/search/suggest?q=iotj     — 实时建议（即时）
POST /api/v1/search/start               — 搜索 → 下载 → 解压（同步等待）
"""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.search_service import list_all_journals, llm_resolve_query, match_all, search_template_links
from app.services.downloader import download_and_extract
from app.services import task_service, template_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/suggest")
async def suggest_journals(q: str = Query(..., min_length=1)):
    """输入期刊名或缩写，返回匹配列表"""
    results = match_all(q)
    return [
        {"id": r["id"], "name": r["name"], "match": "direct"}
        for r in results[:8]
    ]


@router.get("/journals")
async def list_journals():
    """列出所有已知期刊模板"""
    return list_all_journals()


# ---------------------------------------------------------------------------
# 搜索 + 下载
# ---------------------------------------------------------------------------
class SearchStartRequest(BaseModel):
    journal_name: str = Field(..., max_length=256, examples=["iotj"])
    template_format: str = Field(default="latex", max_length=16)
    user_config_id: str | None = Field(None)
    use_llm_resolve: bool = Field(True)
    download_path: str | None = Field(None, description="用户指定的下载目录")


class SearchStartResponse(BaseModel):
    task_id: str
    status: str
    message: str
    journal_resolved: str | None = None
    found_urls: list[str] = []
    download_path: str | None = None
    extract_dir: str | None = None
    error: str | None = None


@router.post("/start", response_model=SearchStartResponse)
async def start_search(payload: SearchStartRequest, db: AsyncSession = Depends(get_db)):
    """搜索并下载模板。同步执行，直接返回结果。

    1. 别名匹配 → 获取下载链接
    2. 如果无匹配 + 开启了 LLM 解析 → 用大模型将缩写解析为全称 → 再次匹配
    3. 从 CTAN 镜像下载压缩包 → 解压到 workdir
    4. 创建 TemplateMetadata 记录
    """
    journal_name = payload.journal_name.strip()
    if not journal_name:
        raise HTTPException(400, "请输入期刊名称")

    user_id = UUID(payload.user_config_id) if payload.user_config_id else None
    task = await task_service.create_task(
        db, journal_name=journal_name,
        template_format=payload.template_format, user_config_id=user_id,
    )
    await task_service.transition_task_status(db, task, "searching")

    # Step 1: 直接别名匹配
    matches = match_all(journal_name)
    resolved_name = journal_name

    # Step 2: 无匹配 → LLM 解析
    if not matches and payload.use_llm_resolve:
        llm_config = None
        if payload.user_config_id:
            from app.services.user_config_service import get_user_config_with_llm_configs
            try:
                uid = UUID(payload.user_config_id)
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
            resolved_name = resolved
            matches = match_all(resolved_name)

    # Step 3: 获取下载链接
    candidates = search_template_links(resolved_name, payload.template_format)
    if not matches and not candidates:
        await task_service.transition_task_status(db, task, "failed",
            error_message=f"未找到「{journal_name}」的模板。试试输入完整期刊名，或手动选择 .tex 文件。")
        return SearchStartResponse(
            task_id=str(task.id), status="failed",
            message=f"未找到「{journal_name}」的模板",
            journal_resolved=resolved_name if resolved_name != journal_name else None,
            error="未找到匹配的期刊模板",
        )

    found_urls = [c["url"] for c in candidates[:3]]

    # Step 4: 下载第一个有效链接
    last_error = ""
    for url in found_urls:
        try:
            logger.info("Downloading: %s", url)
            dl_result = await download_and_extract(url, resolved_name, payload.template_format, download_dir=payload.download_path)

            # Create template record
            tmpl = await template_service.create_template(
                db,
                journal_name=resolved_name,
                template_format=payload.template_format,
                download_path=dl_result["extract_dir"],
            )
            await task_service.update_task(db, task, template_metadata_id=tmpl.id)
            await task_service.transition_task_status(db, task, "completed")

            return SearchStartResponse(
                task_id=str(task.id), status="completed",
                message=f"已下载并解压到 {dl_result['extract_dir']}",
                journal_resolved=resolved_name if resolved_name != journal_name else None,
                found_urls=found_urls,
                download_path=dl_result["archive_path"],
                extract_dir=dl_result["extract_dir"],
            )
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Download failed for %s: %s", url, exc)
            continue

    # All URLs failed
    await task_service.transition_task_status(db, task, "failed",
        error_message=f"下载失败：{last_error}")
    return SearchStartResponse(
        task_id=str(task.id), status="failed",
        message="所有下载链接均失败",
        journal_resolved=resolved_name if resolved_name != journal_name else None,
        found_urls=found_urls,
        error=f"下载失败：{last_error[:200]}",
    )
