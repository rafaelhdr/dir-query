import asyncio

from sqlalchemy import select

import app.rag.index_service as index_service
from app.db.models import Chunk, Conversation, Exchange, File, Workspace
from app.db.session import async_session_factory

EMBEDDING = [0.0] * 384


class _StubEmbedModel:
    def get_query_embedding(self, text: str) -> list[float]:
        return EMBEDDING

    def get_text_embedding(self, text: str) -> list[float]:
        return EMBEDDING


class _StubMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _StubChatResponse:
    def __init__(self, text: str) -> None:
        self.message = _StubMessage(text)


class _StubLLM:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def achat(self, messages) -> _StubChatResponse:
        return _StubChatResponse("<think>internal reasoning</think>\nThe real answer.")


class _StubNode:
    def get_content(self) -> str:
        return "stub chunk content"


async def _seed_workspace_with_chunk() -> int:
    async with async_session_factory() as session:
        workspace = Workspace(
            name="Company X",
            slug="company-x",
            owner_email="owner@example.com",
            password="irrelevant",
        )
        session.add(workspace)
        await session.flush()

        file = File(
            workspace_id=workspace.id,
            filename="stored.pdf",
            display_name="Report",
            original_filename="report.pdf",
            status="indexed",
        )
        session.add(file)
        await session.flush()

        session.add(
            Chunk(file_id=file.id, chunk_index=0, text="The answer is 42.", embedding=EMBEDDING)
        )
        await session.commit()
        return workspace.id


async def _seed_empty_workspace() -> int:
    async with async_session_factory() as session:
        workspace = Workspace(
            name="Empty Co",
            slug="empty-co",
            owner_email="owner@example.com",
            password="irrelevant",
        )
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        return workspace.id


async def _seed_pending_file(workspace_id: int) -> int:
    async with async_session_factory() as session:
        file = File(
            workspace_id=workspace_id,
            filename="stored.pdf",
            display_name="Report",
            original_filename="report.pdf",
            status="pending",
        )
        session.add(file)
        await session.commit()
        await session.refresh(file)
        return file.id


async def _get_file_status(file_id: int) -> str:
    async with async_session_factory() as session:
        result = await session.execute(select(File).where(File.id == file_id))
        return result.scalar_one().status


async def _seed_conversation(workspace_id: int) -> int:
    async with async_session_factory() as session:
        conversation = Conversation(workspace_id=workspace_id, title="Test conversation")
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation.id


async def _add_exchange(
    conversation_id: int, question: str, answer: str | None, status: str
) -> None:
    async with async_session_factory() as session:
        session.add(
            Exchange(
                conversation_id=conversation_id,
                question=question,
                answer=answer,
                status=status,
            )
        )
        await session.commit()


def test_answer_question_strips_reasoning_and_returns_sources(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _StubLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())

    result = asyncio.run(index_service.answer_question(workspace_id, "What is the answer?"))

    assert result["answer"] == "The real answer."
    assert result["sources"] == [
        {"name": "Report", "url": f"/files/{workspace_id}/stored.pdf"}
    ]


def test_answer_question_without_chunks_returns_placeholder(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_empty_workspace())

    result = asyncio.run(index_service.answer_question(workspace_id, "Anything?"))

    assert result == {"answer": "No documents have been indexed yet.", "sources": []}


def test_answer_question_requires_minimax_api_key_by_default(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "")

    raised: RuntimeError | None = None
    try:
        asyncio.run(index_service.answer_question(1, "Anything?"))
    except RuntimeError as exc:
        raised = exc

    assert raised is not None
    assert "MINIMAX_API_KEY" in str(raised)


def test_answer_question_uses_gemini_when_selected(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(index_service, "GoogleGenAI", _StubLLM)
    monkeypatch.setattr(index_service, "GOOGLE_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())

    result = asyncio.run(index_service.answer_question(workspace_id, "What is the answer?"))

    assert result["answer"] == "The real answer."
    assert result["sources"] == [
        {"name": "Report", "url": f"/files/{workspace_id}/stored.pdf"}
    ]


def test_answer_question_requires_google_api_key_when_gemini_selected(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(index_service, "GOOGLE_API_KEY", "")

    raised: RuntimeError | None = None
    try:
        asyncio.run(index_service.answer_question(1, "Anything?"))
    except RuntimeError as exc:
        raised = exc

    assert raised is not None
    assert "GOOGLE_API_KEY" in str(raised)


def test_index_uploaded_file_fails_cleanly_without_google_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(index_service, "EMBED_PROVIDER", "gemini")
    monkeypatch.setattr(index_service, "GOOGLE_API_KEY", "")
    monkeypatch.setattr(index_service, "_embed_model", None)
    monkeypatch.setattr(index_service._pdf_reader, "load_data", lambda file: ["stub-document"])
    monkeypatch.setattr(
        type(index_service._splitter),
        "get_nodes_from_documents",
        lambda self, documents: [_StubNode()],
    )

    workspace_id = asyncio.run(_seed_empty_workspace())
    file_id = asyncio.run(_seed_pending_file(workspace_id))

    asyncio.run(index_service.index_uploaded_file(file_id, tmp_path / "stored.pdf"))

    assert asyncio.run(_get_file_status(file_id)) == "failed"


def test_answer_question_clears_sources_when_llm_reports_not_found(monkeypatch) -> None:
    class _NotFoundLLM(_StubLLM):
        async def achat(self, messages) -> _StubChatResponse:
            return _StubChatResponse(index_service.NOT_FOUND_ANSWER)

    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _NotFoundLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())

    result = asyncio.run(
        index_service.answer_question(workspace_id, "Can you write a Fibonacci function?")
    )

    assert result["answer"] == index_service.NOT_FOUND_ANSWER
    assert result["sources"] == []


def test_answer_question_without_conversation_id_sends_no_history(monkeypatch) -> None:
    captured: list[list] = []

    class _CapturingLLM(_StubLLM):
        async def achat(self, messages) -> _StubChatResponse:
            captured.append(messages)
            return await super().achat(messages)

    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _CapturingLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())

    asyncio.run(index_service.answer_question(workspace_id, "What is the answer?"))

    # Only the system instruction and the new question, no prior turns.
    assert len(captured[0]) == 2


def test_answer_question_includes_prior_answered_exchanges_as_history(monkeypatch) -> None:
    captured: list[list] = []

    class _CapturingLLM(_StubLLM):
        async def achat(self, messages) -> _StubChatResponse:
            captured.append(messages)
            return await super().achat(messages)

    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _CapturingLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())
    conversation_id = asyncio.run(_seed_conversation(workspace_id))
    asyncio.run(_add_exchange(conversation_id, "First question?", "First answer.", "answered"))

    asyncio.run(
        index_service.answer_question(
            workspace_id, "Second question?", conversation_id=conversation_id
        )
    )

    messages = captured[0]
    # system instruction, prior user, prior assistant, new user question
    assert len(messages) == 4
    assert messages[1].content == "First question?"
    assert messages[2].content == "First answer."


def test_answer_question_caps_history_at_ask_history_limit(monkeypatch) -> None:
    captured: list[list] = []

    class _CapturingLLM(_StubLLM):
        async def achat(self, messages) -> _StubChatResponse:
            captured.append(messages)
            return await super().achat(messages)

    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _CapturingLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")
    monkeypatch.setattr(index_service, "ASK_HISTORY_LIMIT", 1)

    workspace_id = asyncio.run(_seed_workspace_with_chunk())
    conversation_id = asyncio.run(_seed_conversation(workspace_id))
    asyncio.run(_add_exchange(conversation_id, "Older question?", "Older answer.", "answered"))
    asyncio.run(_add_exchange(conversation_id, "Newer question?", "Newer answer.", "answered"))

    asyncio.run(
        index_service.answer_question(
            workspace_id, "Third question?", conversation_id=conversation_id
        )
    )

    messages = captured[0]
    # system instruction, one capped prior exchange (the most recent), new user question
    assert len(messages) == 4
    assert messages[1].content == "Newer question?"
    assert messages[2].content == "Newer answer."


def test_answer_question_excludes_failed_and_pending_exchanges_from_history(monkeypatch) -> None:
    captured: list[list] = []

    class _CapturingLLM(_StubLLM):
        async def achat(self, messages) -> _StubChatResponse:
            captured.append(messages)
            return await super().achat(messages)

    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _CapturingLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())
    conversation_id = asyncio.run(_seed_conversation(workspace_id))
    asyncio.run(_add_exchange(conversation_id, "Failed question?", None, "failed"))
    asyncio.run(_add_exchange(conversation_id, "Pending question?", None, "pending"))

    asyncio.run(
        index_service.answer_question(
            workspace_id, "New question?", conversation_id=conversation_id
        )
    )

    # No answered exchanges exist, so no history is included.
    assert len(captured[0]) == 2
