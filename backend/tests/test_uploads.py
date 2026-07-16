import pytest
from fastapi.testclient import TestClient

import app.api.uploads as uploads_module
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(uploads_module, "UPLOAD_DIR", tmp_path)

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


def test_upload_pdf_is_stored(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    content = b"%PDF-1.4 fake content"
    response = client.post(
        f"/w/{slug}/uploads",
        files={"file": ("report.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "report.pdf"
    assert body["size"] == len(content)
    assert body["filename"].endswith("-report.pdf")
    stored_files = list(tmp_path.rglob(body["filename"]))
    assert len(stored_files) == 1


def test_non_pdf_extension_is_rejected(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/uploads",
        files={"file": ("report.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert list(tmp_path.rglob("*.pdf")) == []


def test_non_pdf_content_type_is_rejected(client: TestClient, tmp_path) -> None:
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/uploads",
        files={"file": ("report.pdf", b"not really a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert list(tmp_path.rglob("*.pdf")) == []


def test_oversized_upload_is_rejected(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(uploads_module, "MAX_UPLOAD_BYTES", 10)
    slug = _create_workspace(client)
    response = client.post(
        f"/w/{slug}/uploads",
        files={"file": ("report.pdf", b"this is definitely over ten bytes", "application/pdf")},
    )

    assert response.status_code == 413
    assert list(tmp_path.rglob("*.pdf")) == []


def test_upload_to_nonexistent_workspace_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/w/does-not-exist/uploads",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )

    assert response.status_code == 404


def test_files_from_different_workspaces_do_not_collide(client: TestClient, tmp_path) -> None:
    slug_a = _create_workspace(client, "Company A")
    slug_b = _create_workspace(client, "Company B")
    content = b"%PDF-1.4 fake content"

    resp_a = client.post(
        f"/w/{slug_a}/uploads",
        files={"file": ("report.pdf", content, "application/pdf")},
    )
    resp_b = client.post(
        f"/w/{slug_b}/uploads",
        files={"file": ("report.pdf", content, "application/pdf")},
    )

    path_a = next(tmp_path.rglob(resp_a.json()["filename"]))
    path_b = next(tmp_path.rglob(resp_b.json()["filename"]))
    assert path_a.parent != path_b.parent
