"""
Crypto Vault — Fernet-based encryption for API keys stored in the database.

Derives a stable key from the application secret so encrypted values survive
restarts without external key management.
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

_SECRET = "supersecretkey_for_dev_only"
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        digest = hashlib.sha256(_SECRET.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
        _fernet = Fernet(key)
    return _fernet


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        return ""


def mask(secret: str, visible: int = 4) -> str:
    if not secret:
        return ""
    if len(secret) <= visible:
        return "*" * len(secret)
    return secret[:visible] + "••••••••"