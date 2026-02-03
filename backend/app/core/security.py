from __future__ import annotations

import hashlib
import secrets


def hash_password(password: str) -> str:
    """Return a stable hash of the password."""

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash."""

    return secrets.compare_digest(hash_password(password), password_hash)
