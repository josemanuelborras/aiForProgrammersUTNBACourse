"""Signed, expiring session tokens (HMAC-SHA256 over a JSON payload)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


class InvalidTokenError(Exception):
    """Raised when a token is malformed, tampered with, or unreadable."""


def issue_token(subject: str, secret: str, ttl_seconds: int) -> str:
    """Build a ``payload.signature`` token that proves origin and expiry."""
    payload = {"sub": subject, "exp": int(time.time()) + ttl_seconds}
    payload_b64 = _b64encode(json.dumps(payload).encode("utf-8"))
    signature = _sign(payload_b64, secret)
    return f"{payload_b64}.{signature}"


def decode_token(token: str, secret: str) -> dict:
    """Verify signature and structure, returning the payload.

    Raises ``InvalidTokenError`` for any malformed, tampered, or
    non-dict payload. Expiry is intentionally not checked here so
    callers can distinguish "invalid" from "expired" if needed.
    """
    if not token or "." not in token:
        raise InvalidTokenError("token is malformed")

    payload_b64, _, signature = token.partition(".")
    expected_signature = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidTokenError("token signature mismatch")

    try:
        payload = json.loads(_b64decode(payload_b64))
    except Exception as exc:
        raise InvalidTokenError("token payload is not valid JSON") from exc

    if not isinstance(payload, dict) or "sub" not in payload or "exp" not in payload:
        raise InvalidTokenError("token payload is incomplete")

    return payload


def is_expired(payload: dict) -> bool:
    return time.time() >= payload["exp"]


def _sign(payload_b64: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)
