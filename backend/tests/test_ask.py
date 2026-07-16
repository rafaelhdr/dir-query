import pytest
from fastapi.testclient import TestClient

import app.api.ask as ask_module
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class _StubNode:
    def __init__(self, file_name: str) -> None:
        self.metadata = {"file_name": file_name}


class _StubResponse:
    def __init__(self, text: str, source_nodes: list[_StubNode]) -> None:
        self._text = text
        self.source_nodes = source_nodes

    def __str__(self) -> str:
        return self._text


class _StubQueryEngine:
    def __init__(self, answer: str, sources: list[str]) -> None:
        self._answer = answer
        self._sources = sources

    def query(self, question: str) -> _StubResponse:
        return _StubResponse(self._answer, [_StubNode(name) for name in self._sources])


def test_answers_question_using_query_engine(client: TestClient, monkeypatch) -> None:
    stub_engine = _StubQueryEngine("The answer is 42.", ["report.pdf"])
    monkeypatch.setattr(ask_module.index_service, "get_query_engine", lambda: stub_engine)

    response = client.post("/ask", data={"question": "What is the answer?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The answer is 42."
    assert body["sources"] == ["report.pdf"]


def test_no_documents_indexed_yet(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ask_module.index_service, "get_query_engine", lambda: None)

    response = client.post("/ask", data={"question": "Anything?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "No documents have been indexed yet.", "sources": []}


def test_missing_api_key_returns_clear_error(client: TestClient, monkeypatch) -> None:
    def _raise() -> None:
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(ask_module.index_service, "get_query_engine", _raise)

    response = client.post("/ask", data={"question": "Anything?"})

    assert response.status_code == 503
    assert "MINIMAX_API_KEY" in response.json()["detail"]


def test_reasoning_tags_are_stripped_from_answer(client: TestClient, monkeypatch) -> None:
    raw = "<think>internal reasoning here</think>\nThe real answer."
    stub_engine = _StubQueryEngine(raw, [])
    monkeypatch.setattr(ask_module.index_service, "get_query_engine", lambda: stub_engine)

    response = client.post("/ask", data={"question": "What is it?"})

    assert response.json()["answer"] == "The real answer."
