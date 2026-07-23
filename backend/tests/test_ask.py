import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.api.ask as ask_module
from app.db.models import Exchange, Workspace
from app.db.session import async_session_factory
from app.main import app
from app.services import conversations


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_workspace(client: TestClient, name: str = "Company X") -> str:
    response = client.post(
        "/workspaces",
        data={"name": name},
    )
    return response.json()["slug"]


def _get_workspace_id(slug: str) -> int:
    async def _fetch() -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(Workspace).where(Workspace.slug == slug))
            return result.scalar_one().id

    return asyncio.run(_fetch())


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


def _parse_sse_events(text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for raw_frame in text.split("\n\n"):
        if not raw_frame or raw_frame.startswith(":"):
            continue
        event_type = "message"
        data_lines = []
        for line in raw_frame.split("\n"):
            if line.startswith("event:"):
                event_type = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())
        if not data_lines:
            continue
        events.append({"type": event_type, "data": json.loads("\n".join(data_lines))})
    return events


def _done_event(events: list[dict[str, object]]) -> dict[str, object]:
    for event in events:
        if event["type"] == "done":
            return event["data"]
    raise AssertionError(f"no 'done' event found in {events}")


async def _resolve_llm_ok(workspace_id: int) -> tuple[None, str, str | None]:
    return None, "system", "minimax"


def test_answers_question_using_answer_question(client: TestClient, monkeypatch) -> None:
    async def _stub(llm, key_source, used_provider, workspace_id, question, conversation_id=None):
        yield {"type": "token", "text": "The answer is 42."}
        yield {
            "type": "final",
            "answer": "The answer is 42.",
            "sources": [{"name": "report.pdf", "url": "/files/1/report.pdf"}],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _resolve_llm_ok)
    monkeypatch.setattr(ask_module.conversations.index_service, "answer_question", _stub)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "What is the answer?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse_events(response.text)
    assert {"type": "token", "data": "The answer is 42."} in events
    done = _done_event(events)
    assert done["answer"] == "The answer is 42."
    assert done["sources"] == [{"name": "report.pdf", "url": "/files/1/report.pdf"}]
    assert isinstance(done["conversation_id"], int)
    assert done["title"] == "What is the answer?"


def test_no_documents_indexed_yet(client: TestClient, monkeypatch) -> None:
    async def _stub(llm, key_source, used_provider, workspace_id, question, conversation_id=None):
        yield {"type": "token", "text": "No documents have been indexed yet."}
        yield {
            "type": "final",
            "answer": "No documents have been indexed yet.",
            "sources": [],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _resolve_llm_ok)
    monkeypatch.setattr(ask_module.conversations.index_service, "answer_question", _stub)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})

    assert response.status_code == 200
    done = _done_event(_parse_sse_events(response.text))
    assert done["answer"] == "No documents have been indexed yet."
    assert done["sources"] == []


def test_missing_api_key_returns_clear_error(client: TestClient, monkeypatch) -> None:
    async def _raise(workspace_id: int):
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _raise)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})

    assert response.status_code == 503
    assert "MINIMAX_API_KEY" in response.json()["detail"]


def test_answered_exchange_records_llm_key_source_and_provider(
    client: TestClient, monkeypatch
) -> None:
    async def _resolve_llm(workspace_id: int) -> tuple[None, str, str | None]:
        return None, "dedicated", "gemini"

    async def _stub(llm, key_source, used_provider, workspace_id, question, conversation_id=None):
        yield {"type": "token", "text": "The answer is 42."}
        yield {
            "type": "final",
            "answer": "The answer is 42.",
            "sources": [],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _resolve_llm)
    monkeypatch.setattr(ask_module.conversations.index_service, "answer_question", _stub)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "What is the answer?"})
    assert response.status_code == 200
    _parse_sse_events(response.text)  # drain to ensure the stream fully completed

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
    async def _stub(llm, key_source, used_provider, workspace_id, question, conversation_id=None):
        yield {"type": "token", "text": f"Answer to: {question}"}
        yield {
            "type": "final",
            "answer": f"Answer to: {question}",
            "sources": [],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _resolve_llm_ok)
    monkeypatch.setattr(ask_module.conversations.index_service, "answer_question", _stub)
    slug = _create_workspace(client)

    first = client.post(f"/w/{slug}/ask", data={"question": "First question?"})
    first_done = _done_event(_parse_sse_events(first.text))
    conversation_id = first_done["conversation_id"]

    second = client.post(
        f"/w/{slug}/ask",
        data={"question": "Second question?", "conversation_id": conversation_id},
    )

    assert second.status_code == 200
    second_done = _done_event(_parse_sse_events(second.text))
    assert second_done["conversation_id"] == conversation_id
    assert second_done["title"] == first_done["title"]


def test_ask_nonexistent_conversation_returns_404(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.post(
        f"/w/{slug}/ask",
        data={"question": "Anything?", "conversation_id": 999999},
    )

    assert response.status_code == 404


def test_failed_answer_persists_a_failed_exchange(client: TestClient, monkeypatch) -> None:
    async def _raise(workspace_id: int):
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _raise)
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


def test_generation_completes_and_persists_even_if_nothing_reads_the_queue(
    client: TestClient, monkeypatch
) -> None:
    """Simulates a client that disconnects immediately after the request is
    accepted: calls `conversations.ask` directly and never touches the
    returned queue, then confirms generation still ran to completion and
    the exchange was still persisted."""

    async def _stub(llm, key_source, used_provider, workspace_id, question, conversation_id=None):
        yield {"type": "token", "text": "The full answer."}
        yield {
            "type": "final",
            "answer": "The full answer.",
            "sources": [],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    monkeypatch.setattr(conversations.index_service, "resolve_llm", _resolve_llm_ok)
    monkeypatch.setattr(conversations.index_service, "answer_question", _stub)
    slug = _create_workspace(client)
    workspace_id = _get_workspace_id(slug)

    async def _scenario() -> tuple[str, str | None]:
        tasks_before = set(conversations._background_tasks)
        conversation_id, _title, _queue = await conversations.ask(
            workspace_id, "Anything?", None
        )
        new_tasks = conversations._background_tasks - tasks_before
        assert len(new_tasks) == 1
        await next(iter(new_tasks))

        async with async_session_factory() as session:
            result = await session.execute(
                select(Exchange).where(Exchange.conversation_id == conversation_id)
            )
            exchange = result.scalar_one()
            return exchange.status, exchange.answer

    status, answer = asyncio.run(_scenario())
    assert status == "answered"
    assert answer == "The full answer."
