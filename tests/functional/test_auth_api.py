from conftest import VALID_PASSWORD


def register(client, username=" alice ", password=VALID_PASSWORD):
    return client.post("/register", json={"username": username, "password": password})


def login(client, username="alice", password=VALID_PASSWORD):
    return client.post("/login", json={"username": username, "password": password})


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_register_endpoint_success(client):
    response = register(client)
    assert response.status_code == 201
    assert response.get_json() == {"username": "alice", "created": True}


def test_register_endpoint_rejects_duplicate_user(client):
    register(client)
    response = register(client)
    assert response.status_code == 400
    assert "already exists" in response.get_json()["error"]


def test_register_endpoint_rejects_weak_password(client):
    response = register(client, password="weak")
    assert response.status_code == 400


def test_login_endpoint_success_returns_token(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert response.get_json()["token"]


def test_login_endpoint_rejects_invalid_credentials(client):
    register(client)
    response = login(client, password="wrong-password1")
    assert response.status_code == 401


def test_login_endpoint_locks_account_after_repeated_failures(client):
    register(client)
    for _ in range(3):
        login(client, password="wrong-password1")

    response = login(client)  # correct password, but now locked
    assert response.status_code == 423


def test_validate_endpoint_accepts_a_token_from_login(client):
    register(client)
    token = login(client).get_json()["token"]

    response = client.post("/validate", json={"token": token})
    assert response.status_code == 200
    assert response.get_json() == {"valid": True}


def test_validate_endpoint_rejects_missing_token(client):
    response = client.post("/validate", json={})
    assert response.status_code == 200
    assert response.get_json() == {"valid": False}
