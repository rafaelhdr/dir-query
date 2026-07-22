import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.api.ask as ask_module
from app.db.models import Exchange
from app.db.session import async_session_factory
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_workspace(client: TestClient, name: str = "Company X") -> str:
    response = client.post(
        "/workspaces",
        data={"name": name},
    )
    return response.json()["slug"]


def _get_exchange_status(exchange_id: int) -> str:
    async def _fetch() -> str:
        async with async_session_factory() as session:
            result = await session.execute(select(Exchange).where(Exchange.id == exchange_id))
            return result.scalar_one().status

    return asyncio.run(_fetch())


def _get_exchange_llm_fields(exchange_id: int) -> tuple[str | None, str | None]:
    async def _fetch() -> tuple[str | None, str | None]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Exchange.llm_key_source, Exchange.llm_provider).where(
                    Exchange.id == exchange_id
                )
            )
            return result.one()

    return asyncio.run(_fetch())


def test_answers_question_using_answer_question(client: TestClient, monkeypatch) -> None:
    async def _stub(workspace_id: int, question: str, conversation_id=None) -> dict[str, object]:
        return {
            "answer": "The answer is 42.",
            "sources": [{"name": "report.pdf", "url": "/files/1/report.pdf"}],
        }

    monkeypatch.setattr(
        ask_module.conversations.index_service, "answer_question", _stub
    )
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "What is the answer?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The answer is 42."
    assert body["sources"] == [{"name": "report.pdf", "url": "/files/1/report.pdf"}]
    assert isinstance(body["conversation_id"], int)
    assert body["title"] == "What is the answer?"


def test_no_documents_indexed_yet(client: TestClient, monkeypatch) -> None:
    async def _stub(workspace_id: int, question: str, conversation_id=None) -> dict[str, object]:
        return {"answer": "No documents have been indexed yet.", "sources": []}

    monkeypatch.setattr(
        ask_module.conversations.index_service, "answer_question", _stub
    )
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "No documents have been indexed yet."
    assert body["sources"] == []


def test_missing_api_key_returns_clear_error(client: TestClient, monkeypatch) -> None:
    async def _raise(workspace_id: int, question: str, conversation_id=None) -> dict[str, object]:
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(
        ask_module.conversations.index_service, "answer_question", _raise
    )
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})

    assert response.status_code == 503
    assert "MINIMAX_API_KEY" in response.json()["detail"]


def test_answered_exchange_records_llm_key_source_and_provider(
    client: TestClient, monkeypatch
) -> None:
    async def _stub(workspace_id: int, question: str, conversation_id=None) -> dict[str, object]:
        return {
            "answer": "The answer is 42.",
            "sources": [],
            "llm_key_source": "dedicated",
            "llm_provider": "gemini",
        }

    monkeypatch.setattr(
        ask_module.conversations.index_service, "answer_question", _stub
    )
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "What is the answer?"})
    assert response.status_code == 200

    async def _find_exchange_id() -> int:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Exchange).where(Exchange.question == "What is the answer?")
            )
            return result.scalar_one().id

    exchange_id = asyncio.run(_find_exchange_id())
    llm_key_source, llm_provider = _get_exchange_llm_fields(exchange_id)
    assert llm_key_source == "dedicated"
    assert llm_provider == "gemini"


def test_ask_nonexistent_workspace_returns_404(client: TestClient) -> None:
    response = client.post("/w/does-not-exist/ask", data={"question": "Anything?"})

    assert response.status_code == 404


def test_second_question_reuses_existing_conversation(client: TestClient, monkeypatch) -> None:
    async def _stub(workspace_id: int, question: str, conversation_id=None) -> dict[str, object]:
        return {"answer": f"Answer to: {question}", "sources": []}

    monkeypatch.setattr(
        ask_module.conversations.index_service, "answer_question", _stub
    )
    slug = _create_workspace(client)

    first = client.post(f"/w/{slug}/ask", data={"question": "First question?"})
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        f"/w/{slug}/ask",
        data={"question": "Second question?", "conversation_id": conversation_id},
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id
    assert second.json()["title"] == first.json()["title"]


def test_ask_nonexistent_conversation_returns_404(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.post(
        f"/w/{slug}/ask",
        data={"question": "Anything?", "conversation_id": 999999},
    )

    assert response.status_code == 404


def test_failed_answer_persists_a_failed_exchange(client: TestClient, monkeypatch) -> None:
    async def _raise(workspace_id: int, question: str, conversation_id=None) -> dict[str, object]:
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(
        ask_module.conversations.index_service, "answer_question", _raise
    )
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})
    assert response.status_code == 503

    async def _find_exchange_id() -> int:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Exchange).where(Exchange.question == "Anything?")
            )
            return result.scalar_one().id

    exchange_id = asyncio.run(_find_exchange_id())
    assert _get_exchange_status(exchange_id) == "failed"
