from fastapi.testclient import TestClient


def test_create_workspace(client: TestClient) -> None:
    response = client.post(
        "/workspaces",
        data={"name": "Company X", "owner_email": "owner@example.com", "password": "secret"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Company X"
    assert body["slug"] == "company-x"
    assert "owner_email" not in body
    assert "password" not in body


def test_duplicate_name_is_rejected(client: TestClient) -> None:
    data = {"name": "Company X", "owner_email": "owner@example.com", "password": "secret"}
    client.post("/workspaces", data=data)

    response = client.post("/workspaces", data=data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_missing_required_field_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/workspaces",
        data={"owner_email": "owner@example.com", "password": "secret"},
    )

    assert response.status_code == 422


def test_list_workspaces_when_empty(client: TestClient) -> None:
    response = client.get("/workspaces")

    assert response.status_code == 200
    assert response.json() == []


def test_list_workspaces_when_nonempty(client: TestClient) -> None:
    client.post(
        "/workspaces",
        data={"name": "Company X", "owner_email": "owner@example.com", "password": "secret"},
    )

    response = client.get("/workspaces")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "company-x"
    assert "owner_email" not in body[0]


def test_list_workspaces_orders_most_recent_first(client: TestClient) -> None:
    client.post(
        "/workspaces",
        data={"name": "Company A", "owner_email": "owner@example.com", "password": "secret"},
    )
    client.post(
        "/workspaces",
        data={"name": "Company B", "owner_email": "owner@example.com", "password": "secret"},
    )

    response = client.get("/workspaces")

    assert response.status_code == 200
    slugs = [workspace["slug"] for workspace in response.json()]
    assert slugs == ["company-b", "company-a"]


def test_get_workspace_by_slug(client: TestClient) -> None:
    client.post(
        "/workspaces",
        data={"name": "Company X", "owner_email": "owner@example.com", "password": "secret"},
    )

    response = client.get("/workspaces/company-x")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "company-x"
    assert "owner_email" not in body


def test_get_unknown_workspace_returns_404(client: TestClient) -> None:
    response = client.get("/workspaces/does-not-exist")

    assert response.status_code == 404
