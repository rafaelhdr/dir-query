import datetime

import jwt
from fastapi.testclient import TestClient

from app import config


def test_register_creates_account_and_returns_token(client: TestClient) -> None:
    response = client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@example.com"
    assert body["token"]


def test_register_duplicate_email_is_rejected(client: TestClient) -> None:
    data = {"email": "a@example.com", "password": "secret"}
    client.post("/auth/register", data=data)

    response = client.post("/auth/register", data=data)

    assert response.status_code == 409


def test_register_duplicate_email_is_rejected_case_insensitively(
    client: TestClient,
) -> None:
    client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    )

    response = client.post(
        "/auth/register", data={"email": "A@Example.com", "password": "other"}
    )

    assert response.status_code == 409


def test_register_token_is_usable_immediately(client: TestClient) -> None:
    token = client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    ).json()["token"]

    response = client.post(
        "/workspaces",
        data={"name": "Company X"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.json()["can_edit"] is True


def test_login_succeeds_with_correct_credentials(client: TestClient) -> None:
    client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    )

    response = client.post(
        "/auth/login", data={"email": "a@example.com", "password": "secret"}
    )

    assert response.status_code == 200
    assert response.json()["token"]


def test_login_is_case_insensitive_on_email(client: TestClient) -> None:
    client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    )

    response = client.post(
        "/auth/login", data={"email": "A@Example.com", "password": "secret"}
    )

    assert response.status_code == 200


def test_login_wrong_password_is_rejected_generically(client: TestClient) -> None:
    client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    )

    response = client.post(
        "/auth/login", data={"email": "a@example.com", "password": "wrong"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_is_rejected_with_same_generic_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/login", data={"email": "nope@example.com", "password": "whatever"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def _create_owned_workspace(client: TestClient) -> str:
    token = client.post(
        "/auth/register", data={"email": "a@example.com", "password": "secret"}
    ).json()["token"]
    client.post(
        "/workspaces",
        data={"name": "Company X"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return "company-x"


def test_expired_token_is_rejected_on_protected_endpoint(client: TestClient) -> None:
    slug = _create_owned_workspace(client)
    now = datetime.datetime.now(datetime.timezone.utc)
    expired_token = jwt.encode(
        {"sub": "1", "iat": now - datetime.timedelta(hours=20), "exp": now - datetime.timedelta(hours=2)},
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )

    response = client.delete(
        f"/w/{slug}/files/1",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


def test_tampered_token_is_rejected_on_protected_endpoint(client: TestClient) -> None:
    slug = _create_owned_workspace(client)
    token = client.post(
        "/auth/login", data={"email": "a@example.com", "password": "secret"}
    ).json()["token"]
    tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")

    response = client.delete(
        f"/w/{slug}/files/1",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )

    assert response.status_code == 401
