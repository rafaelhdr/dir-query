import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.api.files as files_module
import app.api.uploads as uploads_module
from app.db.models import Chunk
from app.db.session import async_session_factory
from app.main import app

EMBEDDING = [0.0] * 384


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(uploads_module, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(files_module, "UPLOAD_DIR", tmp_path)

    async def _noop_index(file_id, path) -> None:
        return None

    monkeypatch.setattr(uploads_module.index_service, "index_uploaded_file", _noop_index)
    return TestClient(app)


def _create_workspace(client: TestClient, name: str = "Company X") -> str:
    response = client.post(
        "/workspaces",
        data={"name": name, "owner_email": "owner@example.com", "password": "secret"},
    )
    return response.json()["slug"]


def _upload(client: TestClient, slug: str, filename: str = "report.pdf", name: str | None = None):
    data = {"name": name} if name else {}
    return client.post(
        f"/w/{slug}/uploads",
        files={"file": (filename, b"%PDF-1.4 fake content", "application/pdf")},
        data=data,
    )


def test_list_files_when_empty(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.get(f"/w/{slug}/files")

    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_list_files_returns_uploaded_files(client: TestClient) -> None:
    slug = _create_workspace(client)
    upload_response = _upload(client, slug, filename="report.pdf", name="My Report")

    response = client.get(f"/w/{slug}/files")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 1
    entry = body["data"][0]
    assert entry["display_name"] == "My Report"
    assert entry["original_filename"] == "report.pdf"
    assert entry["status"] == "pending"
    assert "id" in entry and "uploaded_at" in entry
    assert entry["url"] == f"/files/1/{upload_response.json()['filename']}"


def test_list_files_for_nonexistent_workspace_returns_404(client: TestClient) -> None:
    response = client.get("/w/does-not-exist/files")

    assert response.status_code == 404


def test_delete_file_removes_row_chunks_and_disk_file(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    upload_response = _upload(client, slug)
    file_id = client.get(f"/w/{slug}/files").json()["data"][0]["id"]
    stored_filename = upload_response.json()["filename"]

    async def _add_chunk() -> None:
        async with async_session_factory() as session:
            session.add(
                Chunk(file_id=file_id, chunk_index=0, text="some text", embedding=EMBEDDING)
            )
            await session.commit()

    asyncio.run(_add_chunk())

    response = client.delete(f"/w/{slug}/files/{file_id}")

    assert response.status_code == 204
    assert client.get(f"/w/{slug}/files").json() == {"data": []}
    assert list(tmp_path.rglob(stored_filename)) == []

    async def _count_chunks() -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(Chunk).where(Chunk.file_id == file_id))
            return len(result.scalars().all())

    assert asyncio.run(_count_chunks()) == 0


def test_delete_nonexistent_file_returns_404(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.delete(f"/w/{slug}/files/9999")

    assert response.status_code == 404


def test_delete_file_from_wrong_workspace_returns_404(client: TestClient) -> None:
    slug_a = _create_workspace(client, "Company A")
    slug_b = _create_workspace(client, "Company B")
    _upload(client, slug_a)
    file_id = client.get(f"/w/{slug_a}/files").json()["data"][0]["id"]

    response = client.delete(f"/w/{slug_b}/files/{file_id}")

    assert response.status_code == 404
    assert len(client.get(f"/w/{slug_a}/files").json()["data"]) == 1
