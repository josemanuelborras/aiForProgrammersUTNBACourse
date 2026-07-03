import time

import pytest

from auth_module import tokens


def test_issue_then_decode_token_roundtrips_the_subject():
    token = tokens.issue_token("alice", "secret", ttl_seconds=60)
    payload = tokens.decode_token(token, "secret")
    assert payload["sub"] == "alice"


def test_decode_token_rejects_wrong_secret():
    token = tokens.issue_token("alice", "secret", ttl_seconds=60)
    with pytest.raises(tokens.InvalidTokenError):
        tokens.decode_token(token, "wrong-secret")


def test_decode_token_rejects_tampered_payload():
    token = tokens.issue_token("alice", "secret", ttl_seconds=60)
    payload_b64, _, signature = token.partition(".")
    tampered = f"{payload_b64}x.{signature}"
    with pytest.raises(tokens.InvalidTokenError):
        tokens.decode_token(tampered, "secret")


def test_decode_token_rejects_malformed_token_without_separator():
    with pytest.raises(tokens.InvalidTokenError):
        tokens.decode_token("not-a-real-token", "secret")


def test_decode_token_rejects_empty_token():
    with pytest.raises(tokens.InvalidTokenError):
        tokens.decode_token("", "secret")


def test_decode_token_rejects_payload_that_is_not_valid_json():
    payload_b64 = "this-is-not-base64-json"
    signature = tokens._sign(payload_b64, "secret")
    with pytest.raises(tokens.InvalidTokenError, match="not valid JSON"):
        tokens.decode_token(f"{payload_b64}.{signature}", "secret")


def test_decode_token_rejects_payload_missing_required_fields():
    payload_b64 = tokens._b64encode(b'{"foo": "bar"}')
    signature = tokens._sign(payload_b64, "secret")
    with pytest.raises(tokens.InvalidTokenError, match="incomplete"):
        tokens.decode_token(f"{payload_b64}.{signature}", "secret")


def test_is_expired_true_for_past_expiry():
    payload = {"sub": "alice", "exp": int(time.time()) - 10}
    assert tokens.is_expired(payload) is True


def test_is_expired_false_for_future_expiry():
    payload = {"sub": "alice", "exp": int(time.time()) + 60}
    assert tokens.is_expired(payload) is False
