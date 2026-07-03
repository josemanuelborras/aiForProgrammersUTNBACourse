import pytest

from auth_module.service import InvalidCredentialsError, LockedAccountError
from conftest import VALID_PASSWORD


# --- register -----------------------------------------------------------

def test_register_success(auth_service):
    result = auth_service.register("alice", VALID_PASSWORD)
    assert result == {"username": "alice", "created": True}


def test_register_normalizes_username_case_and_whitespace(auth_service):
    auth_service.register("  Alice  ", VALID_PASSWORD)
    with pytest.raises(ValueError, match="already exists"):
        auth_service.register("alice", VALID_PASSWORD)


@pytest.mark.parametrize("username,password", [("", VALID_PASSWORD), ("alice", "")])
def test_register_requires_username_and_password(auth_service, username, password):
    with pytest.raises(ValueError, match="required"):
        auth_service.register(username, password)


def test_register_rejects_weak_password(auth_service):
    with pytest.raises(ValueError, match="at least"):
        auth_service.register("alice", "weak")


def test_register_rejects_duplicate_user(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    with pytest.raises(ValueError, match="already exists"):
        auth_service.register("alice", VALID_PASSWORD)


# --- login ----------------------------------------------------------------

def test_login_success_returns_token(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    token = auth_service.login("alice", VALID_PASSWORD)
    assert isinstance(token, str) and token


def test_login_unknown_user_raises_invalid_credentials(auth_service):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("ghost", VALID_PASSWORD)


def test_login_wrong_password_raises_invalid_credentials(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("alice", "wrong-password1")


def test_login_locks_account_after_max_failed_attempts(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            auth_service.login("alice", "wrong-password1")

    with pytest.raises(LockedAccountError):
        auth_service.login("alice", VALID_PASSWORD)


def test_successful_login_resets_failed_attempt_counter(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("alice", "wrong-password1")
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("alice", "wrong-password1")

    auth_service.login("alice", VALID_PASSWORD)  # resets counter

    with pytest.raises(InvalidCredentialsError):
        auth_service.login("alice", "wrong-password1")
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("alice", "wrong-password1")
    # third consecutive failure since the reset -- still not locked yet
    auth_service.login("alice", VALID_PASSWORD)


# --- validate_token ---------------------------------------------------------

def test_validate_token_accepts_a_fresh_token(auth_service):
    auth_service.register("alice", VALID_PASSWORD)
    token = auth_service.login("alice", VALID_PASSWORD)
    assert auth_service.validate_token(token) is True


def test_validate_token_rejects_empty_token(auth_service):
    assert auth_service.validate_token("") is False


def test_validate_token_rejects_garbage_token(auth_service):
    assert auth_service.validate_token("not-a-token") is False


def test_validate_token_rejects_expired_token(expired_token_service):
    expired_token_service.register("alice", VALID_PASSWORD)
    token = expired_token_service.login("alice", VALID_PASSWORD)
    assert expired_token_service.validate_token(token) is False
