import asyncio

import app.rag.index_service as index_service
from app.db.models import Chunk, File, Workspace
from app.db.session import async_session_factory

EMBEDDING = [0.0] * 384


class _StubEmbedModel:
    def get_query_embedding(self, text: str) -> list[float]:
        return EMBEDDING

    def get_text_embedding(self, text: str) -> list[float]:
        return EMBEDDING


class _StubCompletion:
    def __init__(self, text: str) -> None:
        self._text = text

    def __str__(self) -> str:
        return self._text


class _StubLLM:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def acomplete(self, prompt: str) -> _StubCompletion:
        return _StubCompletion("<think>internal reasoning</think>\nThe real answer.")


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
            original_name="report.pdf",
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


def test_answer_question_strips_reasoning_and_returns_sources(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MiniMax", _StubLLM)
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_workspace_with_chunk())

    result = asyncio.run(index_service.answer_question(workspace_id, "What is the answer?"))

    assert result["answer"] == "The real answer."
    assert result["sources"] == ["report.pdf"]


def test_answer_question_without_chunks_returns_placeholder(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "_get_embed_model", lambda: _StubEmbedModel())
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "test-key")

    workspace_id = asyncio.run(_seed_empty_workspace())

    result = asyncio.run(index_service.answer_question(workspace_id, "Anything?"))

    assert result == {"answer": "No documents have been indexed yet.", "sources": []}


def test_answer_question_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr(index_service, "MINIMAX_API_KEY", "")

    raised: RuntimeError | None = None
    try:
        asyncio.run(index_service.answer_question(1, "Anything?"))
    except RuntimeError as exc:
        raised = exc

    assert raised is not None
    assert "MINIMAX_API_KEY" in str(raised)
