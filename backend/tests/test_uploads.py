import pytest
from fastapi.testclient import TestClient

import app.api.uploads as uploads_module
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(uploads_module, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(uploads_module.index_service, "index_uploaded_file", lambda path: None)
    return TestClient(app)


def test_upload_pdf_is_stored(client: TestClient, tmp_path) -> None:
    content = b"%PDF-1.4 fake content"
    response = client.post(
        "/uploads",
        files={"file": ("report.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "report.pdf"
    assert body["size"] == len(content)
    assert body["filename"].endswith("-report.pdf")
    stored_files = list(tmp_path.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].name == body["filename"]


def test_non_pdf_extension_is_rejected(client: TestClient, tmp_path) -> None:
    response = client.post(
        "/uploads",
        files={"file": ("report.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_non_pdf_content_type_is_rejected(client: TestClient, tmp_path) -> None:
    response = client.post(
        "/uploads",
        files={"file": ("report.pdf", b"not really a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_oversized_upload_is_rejected(
    client: TestClient, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(uploads_module, "MAX_UPLOAD_BYTES", 10)
    response = client.post(
        "/uploads",
        files={"file": ("report.pdf", b"this is definitely over ten bytes", "application/pdf")},
    )

    assert response.status_code == 413
    assert list(tmp_path.iterdir()) == []
