"""Password hashing and strength checks for the auth module."""
from __future__ import annotations

import hashlib
import hmac
import secrets

_PBKDF2_ITERATIONS = 100_000
_MIN_PASSWORD_LENGTH = 8


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Derive a PBKDF2-SHA256 hash for ``password``.

    Reuses ``salt`` when supplied so a stored (hash, salt) pair can be
    re-verified; otherwise generates a fresh random salt for a new user.
    """
    if not password:
        raise ValueError("password is required")

    effective_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        effective_salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    ).hex()
    return digest, effective_salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Constant-time comparison against a previously stored hash."""
    if not password:
        return False
    digest, _ = hash_password(password, salt=salt)
    return hmac.compare_digest(digest, stored_hash)


def validate_password_strength(password: str) -> list[str]:
    """Return a list of human-readable violations; empty list means valid."""
    violations = []
    if len(password) < _MIN_PASSWORD_LENGTH:
        violations.append(f"password must be at least {_MIN_PASSWORD_LENGTH} characters")
    if not any(char.isdigit() for char in password):
        violations.append("password must contain at least one digit")
    if not any(char.isalpha() for char in password):
        violations.append("password must contain at least one letter")
    return violations
