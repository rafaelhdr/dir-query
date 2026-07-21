from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "owner@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register", data={"email": email, "password": "secret"}
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace(client: TestClient) -> None:
    response = client.post("/workspaces", data={"name": "Company X"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Company X"
    assert body["slug"] == "company-x"
    assert "owner_email" not in body
    assert "owner_user_id" not in body
    assert "password" not in body


def test_create_workspace_while_logged_in_sets_ownership_and_can_edit(
    client: TestClient,
) -> None:
    headers = _register(client)

    response = client.post("/workspaces", data={"name": "Company X"}, headers=headers)

    assert response.status_code == 201
    assert response.json()["can_edit"] is True


def test_create_workspace_while_logged_out_is_ownerless_and_editable_by_anyone(
    client: TestClient,
) -> None:
    response = client.post("/workspaces", data={"name": "Company X"})

    assert response.status_code == 201
    assert response.json()["can_edit"] is True


def test_duplicate_name_is_rejected(client: TestClient) -> None:
    data = {"name": "Company X"}
    client.post("/workspaces", data=data)

    response = client.post("/workspaces", data=data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_missing_required_field_is_rejected(client: TestClient) -> None:
    response = client.post("/workspaces", data={})

    assert response.status_code == 422


def test_list_workspaces_when_empty(client: TestClient) -> None:
    response = client.get("/workspaces")

    assert response.status_code == 200
    assert response.json() == []


def test_list_workspaces_when_nonempty(client: TestClient) -> None:
    client.post("/workspaces", data={"name": "Company X"})

    response = client.get("/workspaces")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "company-x"
    assert "owner_email" not in body[0]


def test_list_workspaces_orders_most_recent_first(client: TestClient) -> None:
    client.post("/workspaces", data={"name": "Company A"})
    client.post("/workspaces", data={"name": "Company B"})

    response = client.get("/workspaces")

    assert response.status_code == 200
    slugs = [workspace["slug"] for workspace in response.json()]
    assert slugs == ["company-b", "company-a"]


def test_get_workspace_by_slug(client: TestClient) -> None:
    client.post("/workspaces", data={"name": "Company X"})

    response = client.get("/workspaces/company-x")

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "company-x"
    assert "owner_email" not in body


def test_get_unknown_workspace_returns_404(client: TestClient) -> None:
    response = client.get("/workspaces/does-not-exist")

    assert response.status_code == 404


def test_owner_sees_can_edit_true(client: TestClient) -> None:
    headers = _register(client)
    client.post("/workspaces", data={"name": "Company X"}, headers=headers)

    response = client.get("/workspaces/company-x", headers=headers)

    assert response.json()["can_edit"] is True


def test_non_owner_sees_can_edit_false(client: TestClient) -> None:
    owner_headers = _register(client, "owner@example.com")
    other_headers = _register(client, "other@example.com")
    client.post("/workspaces", data={"name": "Company X"}, headers=owner_headers)

    response = client.get("/workspaces/company-x", headers=other_headers)

    assert response.json()["can_edit"] is False


def test_anonymous_visitor_sees_can_edit_false_for_owned_workspace(
    client: TestClient,
) -> None:
    owner_headers = _register(client)
    client.post("/workspaces", data={"name": "Company X"}, headers=owner_headers)

    response = client.get("/workspaces/company-x")

    assert response.json()["can_edit"] is False


def test_anyone_sees_can_edit_true_for_ownerless_workspace(
    client: TestClient,
) -> None:
    client.post("/workspaces", data={"name": "Company X"})

    response = client.get("/workspaces/company-x")

    assert response.json()["can_edit"] is True


def test_owner_identity_never_appears_in_responses(client: TestClient) -> None:
    headers = _register(client)
    create_response = client.post(
        "/workspaces", data={"name": "Company X"}, headers=headers
    )
    list_response = client.get("/workspaces")
    detail_response = client.get("/workspaces/company-x")

    for body in (
        create_response.json(),
        list_response.json()[0],
        detail_response.json(),
    ):
        assert "owner_user_id" not in body
        assert "owner_email" not in body
        assert "owner" not in body
