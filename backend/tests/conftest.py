import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import engine
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_database():
    yield

    async def _truncate() -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text("TRUNCATE workspaces, files, chunks RESTART IDENTITY CASCADE")
            )

    asyncio.run(_truncate())
