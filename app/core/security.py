"""
Symmetric encryption utilities for API-key storage.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` library.
The encryption key is derived from `settings.SECRET_KEY`.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _derive_fernet_key(raw: str) -> bytes:
    """Derive a 32-byte URL-safe base64 Fernet key from a raw secret string."""
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


_cipher: Fernet | None = None


def _get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        _cipher = Fernet(_derive_fernet_key(settings.SECRET_KEY))
    return _cipher


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string and return a Fernet token (URL-safe base64)."""
    if not plaintext:
        return ""
    return _get_cipher().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt a Fernet token back to the original plaintext."""
    if not token:
        return ""
    # cryptography's Fernet raises InvalidToken on tampering / wrong key
    return _get_cipher().decrypt(token.encode("utf-8")).decode("utf-8")
