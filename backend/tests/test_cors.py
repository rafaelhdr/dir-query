from fastapi.testclient import TestClient

_THIRD_PARTY_ORIGIN = "https://example-embedder.test"


def test_workspace_detail_allows_cross_origin_requests(client: TestClient) -> None:
    client.post("/workspaces", data={"name": "Company X"})

    response = client.get(
        "/workspaces/company-x", headers={"Origin": _THIRD_PARTY_ORIGIN}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_ask_endpoint_allows_cross_origin_requests(client: TestClient) -> None:
    create_response = client.post("/workspaces", data={"name": "Company X"})
    slug = create_response.json()["slug"]

    response = client.post(
        f"/w/{slug}/ask",
        data={"question": "What is this about?"},
        headers={"Origin": _THIRD_PARTY_ORIGIN},
    )

    assert response.headers["access-control-allow-origin"] == "*"
