"""Baseline suite: only the happy paths.

Kept separate and unchanged so `pytest tests/unit/test_service_baseline.py
--cov` reproduces the "before optimization" coverage number quoted in the
README, without needing git history.
"""
from conftest import VALID_PASSWORD


def test_register_returns_created_user(auth_service):
    result = auth_service.register("alice", VALID_PASSWORD)
    assert result == {"username": "alice", "created": True}


def test_login_returns_a_token(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    token = auth_service.login("alice", VALID_PASSWORD)
    assert isinstance(token, str) and token


def test_validate_token_accepts_a_fresh_token(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    token = auth_service.login("alice", VALID_PASSWORD)
    assert auth_service.validate_token(token) is True
