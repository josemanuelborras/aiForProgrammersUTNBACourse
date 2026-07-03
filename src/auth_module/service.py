"""Core authentication service: registration, login, token validation."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import tokens
from .security import hash_password, validate_password_strength, verify_password

_MAX_FAILED_ATTEMPTS = 3


class AuthError(Exception):
    """Base class for authentication failures."""


class InvalidCredentialsError(AuthError):
    """Username unknown, or password does not match."""


class LockedAccountError(AuthError):
    """Too many consecutive failed login attempts."""


@dataclass
class _UserRecord:
    username: str
    password_hash: str
    salt: str
    failed_attempts: int = field(default=0)
    locked: bool = field(default=False)


class AuthService:
    def __init__(self, token_secret: str = "dev-secret", token_ttl_seconds: int = 1800) -> None:
        self._users: dict[str, _UserRecord] = {}
        self._token_secret = token_secret
        self._token_ttl_seconds = token_ttl_seconds

    def register(self, username: str, password: str) -> dict:
        normalized = self._normalize_username(username)
        if not normalized or not password:
            raise ValueError("username and password are required")

        violations = validate_password_strength(password)
        if violations:
            raise ValueError("; ".join(violations))

        if normalized in self._users:
            raise ValueError("user already exists")

        password_hash, salt = hash_password(password)
        self._users[normalized] = _UserRecord(username=normalized, password_hash=password_hash, salt=salt)
        return {"username": normalized, "created": True}

    def login(self, username: str, password: str) -> str:
        normalized = self._normalize_username(username)
        user = self._users.get(normalized)
        if not user:
            raise InvalidCredentialsError("invalid credentials")

        if user.locked:
            raise LockedAccountError("account is locked after too many failed attempts")

        if not verify_password(password, user.password_hash, user.salt):
            user.failed_attempts += 1
            if user.failed_attempts >= _MAX_FAILED_ATTEMPTS:
                user.locked = True
            raise InvalidCredentialsError("invalid credentials")

        user.failed_attempts = 0
        return tokens.issue_token(normalized, self._token_secret, self._token_ttl_seconds)

    def validate_token(self, token: str) -> bool:
        if not token:
            return False
        try:
            payload = tokens.decode_token(token, self._token_secret)
        except tokens.InvalidTokenError:
            return False
        return not tokens.is_expired(payload)

    @staticmethod
    def _normalize_username(username: str) -> str:
        return (username or "").strip().lower()
