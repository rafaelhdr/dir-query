import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import config
from app.db.session import engine
from app.main import app

if not config.POSTGRES_DB.endswith("_test"):
    raise RuntimeError(
        f"Refusing to run tests against POSTGRES_DB={config.POSTGRES_DB!r}. "
        "This test suite truncates workspaces/files/chunks/conversations/"
        "exchanges after every test, "
        "so it must never point at a dev or prod database. Set POSTGRES_DB to "
        "a name ending in '_test' (e.g. POSTGRES_DB=understand_your_stuffs_test) "
        "before running pytest."
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_database():
    yield

    async def _truncate() -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "TRUNCATE workspaces, files, chunks, conversations, exchanges "
                    "RESTART IDENTITY CASCADE"
                )
            )

    asyncio.run(_truncate())
