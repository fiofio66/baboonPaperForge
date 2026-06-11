"""
File upload & extract endpoint — accepts uploaded ZIP, saves to workdir, extracts.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.core.config import settings
from app.services.downloader import extract_archive

router = APIRouter(prefix="/files", tags=["files"])


class ExtractResponse(BaseModel):
    extract_dir: str
    main_tex: str | None
    tex_files: list[str]
    file_count: int


@router.post("/extract-zip", response_model=ExtractResponse)
async def extract_zip(file: UploadFile = File(...)):
    """Accept an uploaded ZIP archive, save to workdir, extract, find main.tex.

    Use this from the frontend file picker — the browser sends the actual
    file bytes, not just a filename.
    """
    if not file.filename:
        raise HTTPException(400, "No file provided")

    fname = file.filename.lower()
    if not any(fname.endswith(ext) for ext in (".zip", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
        raise HTTPException(400, f"不支持的格式：{file.filename}。仅支持 .zip / .tar.gz / .tar.bz2 / .tar.xz")

    # Save uploaded file to workdir
    workdir = Path(settings.TEMPLATE_WORKDIR).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    # Sanitize destination name
    safe_name = Path(file.filename).stem.split(".")[0].replace(" ", "_")[:64]
    dest = workdir / safe_name

    # Save uploaded bytes to temp file first
    tmp = workdir / file.filename
    try:
        with open(tmp, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise HTTPException(500, "文件保存失败，请重试")

    # Extract
    try:
        extract_dir = extract_archive(tmp, dest)
    except ValueError as e:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, str(e))

    # Clean up temp archive
    tmp.unlink(missing_ok=True)

    # Find main.tex
    tex_files = sorted(
        [str(p.relative_to(extract_dir)) for p in extract_dir.rglob("*.tex")],
        key=lambda x: ("main" not in x.lower(), x.lower()),
    )
    main_tex = str(extract_dir / tex_files[0]) if tex_files else None
    file_count = sum(1 for _ in extract_dir.rglob("*") if _.is_file())

    return ExtractResponse(
        extract_dir=str(extract_dir),
        main_tex=main_tex,
        tex_files=tex_files,
        file_count=file_count,
    )
