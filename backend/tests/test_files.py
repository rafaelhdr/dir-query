import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.api.files as files_module
from app.db.models import Chunk
from app.db.session import async_session_factory
from app.main import app

EMBEDDING = [0.0] * 384


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(files_module, "UPLOAD_DIR", tmp_path)

    async def _noop_index(file_id, path) -> None:
        return None

    monkeypatch.setattr(files_module.index_service, "index_uploaded_file", _noop_index)
    return TestClient(app)


def _create_workspace(client: TestClient, name: str = "Company X") -> str:
    response = client.post("/workspaces", data={"name": name})
    return response.json()["slug"]


def _register(client: TestClient, email: str = "owner@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register", data={"email": email, "password": "secret"}
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _create_owned_workspace(
    client: TestClient, name: str = "Company X"
) -> tuple[str, dict[str, str]]:
    headers = _register(client)
    response = client.post("/workspaces", data={"name": name}, headers=headers)
    return response.json()["slug"], headers


def _upload(
    client: TestClient,
    slug: str,
    filename: str = "report.pdf",
    name: str | None = None,
    headers: dict[str, str] | None = None,
):
    data = {"name": name} if name else {}
    return client.post(
        f"/w/{slug}/files",
        files={"file": (filename, b"%PDF-1.4 fake content", "application/pdf")},
        data=data,
        headers=headers,
    )


def test_upload_pdf_is_stored(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    content = b"%PDF-1.4 fake content"
    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["display_name"] == "report.pdf"
    assert body["original_filename"] == "report.pdf"
    assert body["size"] == len(content)
    assert body["filename"].endswith("-report.pdf")
    stored_files = list(tmp_path.rglob(body["filename"]))
    assert len(stored_files) == 1


def test_non_pdf_extension_is_rejected(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert list(tmp_path.rglob("*.pdf")) == []


def test_non_pdf_content_type_is_rejected(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"not really a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert list(tmp_path.rglob("*.pdf")) == []


def test_oversized_upload_is_rejected(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(files_module, "MAX_UPLOAD_BYTES", 10)
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"this is definitely over ten bytes", "application/pdf")},
    )

    assert response.status_code == 413
    assert list(tmp_path.rglob("*.pdf")) == []


def test_upload_to_nonexistent_workspace_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/w/does-not-exist/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )

    assert response.status_code == 404


def test_upload_with_custom_name_is_used_as_display_name(client: TestClient) -> None:
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"name": "My Custom Name"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["display_name"] == "My Custom Name"
    assert body["original_filename"] == "report.pdf"


def test_duplicate_display_name_is_rejected(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"name": "Report"},
    )

    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("other.pdf", b"%PDF-1.4 other content", "application/pdf")},
        data={"name": "Report"},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    assert len(list(tmp_path.rglob("*other.pdf"))) == 0


def test_duplicate_original_filename_is_rejected_independently_of_display_name(
    client: TestClient, tmp_path
) -> None:
    slug = _create_workspace(client)
    client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"name": "First Upload"},
    )

    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 other content", "application/pdf")},
        data={"name": "Second Upload"},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    assert len(list(tmp_path.rglob("*.pdf"))) == 1


def test_same_display_name_is_allowed_across_different_workspaces(client: TestClient) -> None:
    slug_a = _create_workspace(client, "Company A")
    slug_b = _create_workspace(client, "Company B")

    resp_a = client.post(
        f"/w/{slug_a}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"name": "Report"},
    )
    resp_b = client.post(
        f"/w/{slug_b}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"name": "Report"},
    )

    assert resp_a.status_code == 201
    assert resp_b.status_code == 201


def test_files_from_different_workspaces_do_not_collide(client: TestClient, tmp_path) -> None:
    slug_a = _create_workspace(client, "Company A")
    slug_b = _create_workspace(client, "Company B")
    content = b"%PDF-1.4 fake content"

    resp_a = client.post(
        f"/w/{slug_a}/files",
        files={"file": ("report.pdf", content, "application/pdf")},
    )
    resp_b = client.post(
        f"/w/{slug_b}/files",
        files={"file": ("report.pdf", content, "application/pdf")},
    )

    path_a = next(tmp_path.rglob(resp_a.json()["filename"]))
    path_b = next(tmp_path.rglob(resp_b.json()["filename"]))
    assert path_a.parent != path_b.parent


def test_owner_can_upload_to_their_own_workspace(client: TestClient) -> None:
    slug, headers = _create_owned_workspace(client)

    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 201


def test_anonymous_upload_to_owned_workspace_is_rejected(client: TestClient) -> None:
    slug, _ = _create_owned_workspace(client)

    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )

    assert response.status_code == 401


def test_non_owner_upload_to_owned_workspace_is_rejected(client: TestClient) -> None:
    slug, _ = _create_owned_workspace(client)
    other_headers = _register(client, "other@example.com")

    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        headers=other_headers,
    )

    assert response.status_code == 403


def test_anyone_can_upload_to_ownerless_workspace(client: TestClient) -> None:
    slug = _create_workspace(client)

    response = client.post(
        f"/w/{slug}/files",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )

    assert response.status_code == 201


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


def test_owner_can_delete_a_file_in_their_own_workspace(client: TestClient) -> None:
    slug, headers = _create_owned_workspace(client)
    _upload(client, slug, headers=headers)
    file_id = client.get(f"/w/{slug}/files").json()["data"][0]["id"]

    response = client.delete(f"/w/{slug}/files/{file_id}", headers=headers)

    assert response.status_code == 204


def test_anonymous_delete_from_owned_workspace_is_rejected(client: TestClient) -> None:
    slug, headers = _create_owned_workspace(client)
    _upload(client, slug, headers=headers)
    file_id = client.get(f"/w/{slug}/files").json()["data"][0]["id"]

    response = client.delete(f"/w/{slug}/files/{file_id}")

    assert response.status_code == 401
    assert len(client.get(f"/w/{slug}/files").json()["data"]) == 1


def test_non_owner_delete_from_owned_workspace_is_rejected(client: TestClient) -> None:
    slug, headers = _create_owned_workspace(client)
    _upload(client, slug, headers=headers)
    file_id = client.get(f"/w/{slug}/files").json()["data"][0]["id"]
    other_headers = _register(client, "other@example.com")

    response = client.delete(f"/w/{slug}/files/{file_id}", headers=other_headers)

    assert response.status_code == 403
    assert len(client.get(f"/w/{slug}/files").json()["data"]) == 1


def test_anyone_can_delete_from_ownerless_workspace(client: TestClient) -> None:
    slug = _create_workspace(client)
    _upload(client, slug)
    file_id = client.get(f"/w/{slug}/files").json()["data"][0]["id"]

    response = client.delete(f"/w/{slug}/files/{file_id}")

    assert response.status_code == 204


def test_listing_files_is_unrestricted_regardless_of_ownership(
    client: TestClient,
) -> None:
    slug, headers = _create_owned_workspace(client)
    _upload(client, slug, headers=headers)

    response = client.get(f"/w/{slug}/files")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
