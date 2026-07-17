import asyncio

from sqlalchemy import text

import scripts.reset_embeddings as reset_embeddings
from app.db.models import Chunk, File, Workspace
from app.db.session import async_session_factory, engine

DEFAULT_DIM = 384


class _StubEmbedModel:
    def __init__(self, dim: int) -> None:
        self._dim = dim

    def get_text_embedding(self, text: str) -> list[float]:
        return [0.0] * self._dim


async def _seed_chunk() -> int:
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
            Chunk(file_id=file.id, chunk_index=0, text="hi", embedding=[0.0] * DEFAULT_DIM)
        )
        await session.commit()
        return file.id


async def _chunk_count() -> int:
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT count(*) FROM chunks"))
        return result.scalar_one()


async def _embedding_column_type() -> str:
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                "WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'"
            )
        )
        return result.scalar_one()


async def _file_status(file_id: int) -> str:
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT status FROM files WHERE id = :id"), {"id": file_id})
        return result.scalar_one()


def test_reset_embeddings_clears_chunks_resizes_column_and_resets_files(monkeypatch) -> None:
    monkeypatch.setattr(reset_embeddings, "_get_embed_model", lambda: _StubEmbedModel(768))

    file_id = asyncio.run(_seed_chunk())

    # The column dimension change is global (real DB, not per-test isolated), so
    # restore it in `finally` even if an assertion fails, or later tests using
    # the default 384-dim embedding fixtures would break.
    try:
        target_dim = reset_embeddings._target_dimension()
        asyncio.run(reset_embeddings.reset_embeddings(target_dim))

        assert target_dim == 768
        assert asyncio.run(_chunk_count()) == 0
        assert asyncio.run(_embedding_column_type()) == "vector(768)"
        assert asyncio.run(_file_status(file_id)) == "pending"
    finally:
        asyncio.run(reset_embeddings.reset_embeddings(DEFAULT_DIM))
