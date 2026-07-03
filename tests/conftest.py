import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auth_module.api import create_app
from auth_module.service import AuthService

VALID_PASSWORD = "Sup3rSecret"


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(token_secret="test-secret", token_ttl_seconds=1800)


@pytest.fixture
def expired_token_service() -> AuthService:
    """Issues tokens that are already expired, to test expiry handling."""
    return AuthService(token_secret="test-secret", token_ttl_seconds=-1)


@pytest.fixture
def app(auth_service):
    flask_app = create_app(auth_service)
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
