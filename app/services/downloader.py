"""
Safe archive downloader + extractor.

Downloads template archives from candidate URLs, extracts them to the
local workdir, with security checks (size limit, zip-slip prevention).
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
DOWNLOAD_TIMEOUT = 180.0  # seconds — many template archives are 10-50MB
CHUNK_SIZE = 64 * 1024  # 64 KB
_USER_AGENT = (
    "Mozilla/5.0 (compatible; BaboonPaperForge/0.1; +https://github.com/fiofio66/baboonPaperForge)"
)


def _is_safe_extract_path(base_dir: Path, member_path: Path) -> bool:
    """Prevent zip-slip: ensure the extracted path stays inside base_dir."""
    resolved = (base_dir / member_path).resolve()
    return str(resolved).startswith(str(base_dir.resolve()))


async def download_file(url: str, dest_dir: Path, filename: str | None = None) -> Path:
    """Download a file from `url` into `dest_dir`.

    Args:
        url: The file URL.
        dest_dir: Directory to save to.
        filename: Optional output filename. Auto-detected from URL if omitted.

    Returns:
        Path to the downloaded file.

    Raises:
        httpx.HTTPError: On HTTP errors.
        ValueError: If the response exceeds ``MAX_FILE_SIZE``.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        # Derive filename from URL
        url_path = url.split("?")[0]
        filename = url_path.rsplit("/", 1)[-1] or "download.zip"
        if not filename.endswith((".zip", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".gz")):
            filename += ".zip"

    dest_path = dest_dir / filename

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=30.0, read=DOWNLOAD_TIMEOUT, write=60.0, pool=30.0),
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=True,
    ) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            total = 0
            with open(dest_path, "wb") as f:
                async for chunk in resp.aiter_bytes(CHUNK_SIZE):
                    total += len(chunk)
                    if total > MAX_FILE_SIZE:
                        f.close()
                        dest_path.unlink(missing_ok=True)
                        raise ValueError(
                            f"Download exceeds {MAX_FILE_SIZE // (1024*1024)} MB limit"
                        )
                    f.write(chunk)

    return dest_path


def extract_archive(archive_path: Path, dest_dir: Path | None = None) -> Path:
    """Extract a .zip or .tar.* archive into a destination directory.

    Args:
        archive_path: Path to the archive file.
        dest_dir: Extraction target. Defaults to ``<workdir>/<stem>/``.

    Returns:
        Path to the extraction root directory.

    Raises:
        ValueError: On unsupported format or zip-slip attempt.
    """
    if dest_dir is None:
        workdir = Path(settings.TEMPLATE_WORKDIR).resolve()
        dest_dir = workdir / archive_path.stem.split(".")[0]  # remove .zip / .tar
    dest_dir.mkdir(parents=True, exist_ok=True)

    fname_lower = archive_path.name.lower()

    # ---- .zip ----
    if fname_lower.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.infolist():
                member_path = Path(member.filename)
                # Skip directories (created automatically)
                if member.is_dir():
                    continue
                # Prevent zip-slip
                if not _is_safe_extract_path(dest_dir, member_path):
                    raise ValueError(
                        f"Zip-slip blocked: {member.filename} escapes {dest_dir}"
                    )
                target = dest_dir / member_path
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())
        return dest_dir

    # ---- .tar.* ----
    import tarfile
    if fname_lower.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
        mode_map = {
            ".tar.gz": "r:gz", ".tgz": "r:gz",
            ".tar.bz2": "r:bz2", ".tar.xz": "r:xz", ".tar": "r:",
        }
        mode = "r:*"  # auto-detect
        for ext, m in mode_map.items():
            if fname_lower.endswith(ext):
                mode = m
                break

        with tarfile.open(archive_path, mode) as tf:
            for member in tf.getmembers():
                if member.isdir():
                    continue
                member_path = Path(member.name)
                if not _is_safe_extract_path(dest_dir, member_path):
                    raise ValueError(
                        f"Tar-slip blocked: {member.name} escapes {dest_dir}"
                    )
                target = dest_dir / member_path
                target.parent.mkdir(parents=True, exist_ok=True)
                with tf.extractfile(member) as src, open(target, "wb") as dst:
                    if src:
                        dst.write(src.read())
        return dest_dir

    raise ValueError(f"Unsupported archive format: {archive_path.suffix}")


async def download_and_extract(
    url: str, journal_name: str, template_format: str = "latex"
) -> dict[str, Any]:
    """Download and extract a template archive in one step.

    Returns a dict with ``archive_path`` and ``extract_dir``.
    """
    workdir = Path(settings.TEMPLATE_WORKDIR).resolve()
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", journal_name)[:64]
    journal_dir = workdir / safe_name

    archive_path = await download_file(url, journal_dir)
    extract_dir = extract_archive(archive_path, journal_dir)

    return {
        "archive_path": str(archive_path),
        "extract_dir": str(extract_dir),
        "file_count": sum(1 for _ in extract_dir.rglob("*") if _.is_file()),
    }


import re  # noqa: E402 (used in download_and_extract)
