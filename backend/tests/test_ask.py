import pytest
from fastapi.testclient import TestClient

import app.api.ask as ask_module
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_workspace(client: TestClient, name: str = "Company X") -> str:
    response = client.post(
        "/workspaces",
        data={"name": name, "owner_email": "owner@example.com", "password": "secret"},
    )
    return response.json()["slug"]


def test_answers_question_using_answer_question(client: TestClient, monkeypatch) -> None:
    async def _stub(workspace_id: int, question: str) -> dict[str, object]:
        return {"answer": "The answer is 42.", "sources": ["report.pdf"]}

    monkeypatch.setattr(ask_module.index_service, "answer_question", _stub)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "What is the answer?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The answer is 42."
    assert body["sources"] == ["report.pdf"]


def test_no_documents_indexed_yet(client: TestClient, monkeypatch) -> None:
    async def _stub(workspace_id: int, question: str) -> dict[str, object]:
        return {"answer": "No documents have been indexed yet.", "sources": []}

    monkeypatch.setattr(ask_module.index_service, "answer_question", _stub)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "No documents have been indexed yet.", "sources": []}


def test_missing_api_key_returns_clear_error(client: TestClient, monkeypatch) -> None:
    async def _raise(workspace_id: int, question: str) -> dict[str, object]:
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(ask_module.index_service, "answer_question", _raise)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})

    assert response.status_code == 503
    assert "MINIMAX_API_KEY" in response.json()["detail"]


def test_ask_nonexistent_workspace_returns_404(client: TestClient) -> None:
    response = client.post("/w/does-not-exist/ask", data={"question": "Anything?"})

    assert response.status_code == 404
