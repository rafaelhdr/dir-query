import json

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
        data={"name": name},
    )
    return response.json()["slug"]


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


def _done_event(response) -> dict[str, object]:
    for event in _parse_sse_events(response.text):
        if event["type"] == "done":
            return event["data"]
    raise AssertionError(f"no 'done' event found in response: {response.text!r}")


async def _resolve_llm_ok(workspace_id: int) -> tuple[None, str, str | None]:
    return None, "system", "minimax"


def _stub_answer_question(monkeypatch) -> None:
    async def _stub(llm, key_source, used_provider, workspace_id, question, conversation_id=None):
        yield {"type": "token", "text": f"Answer to: {question}"}
        yield {
            "type": "final",
            "answer": f"Answer to: {question}",
            "sources": [{"name": "report.pdf", "url": "/files/1/report.pdf"}],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _resolve_llm_ok)
    monkeypatch.setattr(ask_module.conversations.index_service, "answer_question", _stub)


def test_list_conversations_for_workspace_with_no_history(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.get(f"/w/{slug}/conversations")

    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_list_conversations_returns_title_and_created_at(client: TestClient, monkeypatch) -> None:
    _stub_answer_question(monkeypatch)
    slug = _create_workspace(client)

    client.post(f"/w/{slug}/ask", data={"question": "What is the refund policy?"})

    response = client.get(f"/w/{slug}/conversations")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "What is the refund policy?"
    assert "created_at" in data[0]


def test_most_recently_active_conversation_listed_first(client: TestClient, monkeypatch) -> None:
    _stub_answer_question(monkeypatch)
    slug = _create_workspace(client)

    first = client.post(f"/w/{slug}/ask", data={"question": "First conversation"})
    client.post(f"/w/{slug}/ask", data={"question": "Second conversation"})
    # Reactivate the first conversation with a follow-up so it becomes most recent.
    client.post(
        f"/w/{slug}/ask",
        data={
            "question": "Follow-up on first",
            "conversation_id": _done_event(first)["conversation_id"],
        },
    )

    response = client.get(f"/w/{slug}/conversations")

    titles = [c["title"] for c in response.json()["data"]]
    assert titles[0] == "First conversation"


def test_get_conversation_returns_full_history(client: TestClient, monkeypatch) -> None:
    _stub_answer_question(monkeypatch)
    slug = _create_workspace(client)

    first = client.post(f"/w/{slug}/ask", data={"question": "First question?"})
    conversation_id = _done_event(first)["conversation_id"]
    client.post(
        f"/w/{slug}/ask",
        data={"question": "Second question?", "conversation_id": conversation_id},
    )

    response = client.get(f"/w/{slug}/conversations/{conversation_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "First question?"
    assert [e["question"] for e in body["exchanges"]] == [
        "First question?",
        "Second question?",
    ]
    assert all(e["status"] == "answered" for e in body["exchanges"])


def test_get_conversation_includes_failed_exchange(client: TestClient, monkeypatch) -> None:
    async def _raise(workspace_id: int):
        raise RuntimeError("MINIMAX_API_KEY is not configured")

    monkeypatch.setattr(ask_module.conversations.index_service, "resolve_llm", _raise)
    slug = _create_workspace(client)

    response = client.post(f"/w/{slug}/ask", data={"question": "Anything?"})
    assert response.status_code == 503

    # Recover the conversation id from the persisted exchange via a fresh
    # request that reuses conversation creation semantics isn't possible
    # here (the failed request didn't return a body), so look it up via
    # the conversation list instead.
    conversations_response = client.get(f"/w/{slug}/conversations")
    conversation_id = conversations_response.json()["data"][0]["id"]

    response = client.get(f"/w/{slug}/conversations/{conversation_id}")

    assert response.status_code == 200
    exchanges = response.json()["exchanges"]
    assert len(exchanges) == 1
    assert exchanges[0]["status"] == "failed"
    assert exchanges[0]["answer"] is None


def test_get_nonexistent_conversation_returns_404(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.get(f"/w/{slug}/conversations/999999")

    assert response.status_code == 404


def test_get_conversation_from_wrong_workspace_returns_404(client: TestClient, monkeypatch) -> None:
    _stub_answer_question(monkeypatch)
    slug_a = _create_workspace(client, name="Workspace A")
    slug_b = _create_workspace(client, name="Workspace B")

    response = client.post(f"/w/{slug_a}/ask", data={"question": "A question"})
    conversation_id = _done_event(response)["conversation_id"]

    response = client.get(f"/w/{slug_b}/conversations/{conversation_id}")

    assert response.status_code == 404


def test_conversations_for_nonexistent_workspace_returns_404(client: TestClient) -> None:
    response = client.get("/w/does-not-exist/conversations")

    assert response.status_code == 404
