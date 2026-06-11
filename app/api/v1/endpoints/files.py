"""
File handling endpoints — zip extraction & directory browser.

POST /api/v1/files/extract-zip  — extract a zip to workdir, find main.tex
POST /api/v1/files/open-dir     — trigger native OS directory picker
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.services.downloader import extract_archive

router = APIRouter(prefix="/files", tags=["files"])


class ExtractRequest(BaseModel):
    zip_path: str


class ExtractResponse(BaseModel):
    extract_dir: str
    main_tex: str | None
    tex_files: list[str]
    file_count: int


@router.post("/extract-zip", response_model=ExtractResponse)
async def extract_zip(payload: ExtractRequest):
    """Extract a ZIP archive and find the main .tex file inside.

    Templates from journals are typically distributed as .zip files.
    This extracts them into the workdir and locates the entry point.
    """
    zip_path = Path(payload.zip_path)
    if not zip_path.exists():
        raise HTTPException(404, f"File not found: {zip_path}")
    if not zip_path.suffix.lower() in (".zip", ".gz", ".tgz", ".bz2", ".xz"):
        raise HTTPException(400, "Only .zip / .tar.gz / .tar.bz2 / .tar.xz archives are supported")

    workdir = Path(settings.TEMPLATE_WORKDIR).resolve()
    safe_name = zip_path.stem.split(".")[0]  # remove .zip / .tar
    # Sanitize: remove version numbers etc
    safe_name = safe_name.replace(" ", "_")[:64]
    dest = workdir / safe_name

    try:
        extract_dir = extract_archive(zip_path, dest)
    except ValueError as e:
        raise HTTPException(400, str(e))

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
