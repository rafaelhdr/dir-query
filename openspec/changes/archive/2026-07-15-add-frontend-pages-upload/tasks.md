## 1. Backend: upload endpoint

- [x] 1.1 Add `UPLOAD_DIR` (default `/data/uploads`) and `MAX_UPLOAD_BYTES` (default 20 MB) settings, read from env vars; `UPLOAD_DIR` is created on first upload if missing (not at import time, so tests can monkeypatch it before any directory is touched)
- [x] 1.2 Create `backend/app/api/uploads.py` with `POST /uploads` (multipart/form-data, field `file`)
- [x] 1.3 Validate filename ends in `.pdf` (case-insensitive) and content-type is `application/pdf`; reject otherwise with a 4xx error and a clear message, without writing the file
- [x] 1.4 Enforce `MAX_UPLOAD_BYTES`; reject oversized uploads with `413` without writing the file
- [x] 1.5 Persist accepted files to `UPLOAD_DIR` as `<uuid4>-<sanitized-original-filename>`, stripping path separators from the original name
- [x] 1.6 Return `201` with `{"filename", "original_filename", "size"}` on success
- [x] 1.7 Register the uploads router in `backend/app/main.py`'s `create_app()`

## 2. Backend: tests

- [x] 2.1 Add `backend/tests/test_uploads.py` covering: accepted PDF is stored, non-PDF rejected, oversized file rejected, response body shape on success
- [x] 2.2 Point `UPLOAD_DIR` at a `tmp_path` fixture in tests so no real storage is touched
- [x] 2.3 Run `uv run pytest -v` and confirm all tests pass

## 3. Docker Compose: storage wiring

- [x] 3.1 Create `backend/data/uploads/.gitkeep` and add `backend/data/uploads/*` (except `.gitkeep`) to `.gitignore`
- [x] 3.2 Bind-mount `./backend/data/uploads` into the `backend` service at `UPLOAD_DIR` (`/data/uploads`) in `docker-compose.yml`
- [x] 3.3 Set `UPLOAD_DIR` (and `MAX_UPLOAD_BYTES` if overridden) as backend service environment variables

## 4. Frontend: shared nav and Nginx proxy

- [x] 4.1 Write a small shared `<nav>` markup snippet (links to `/`, `/ask`, `/feed/upload`) to copy into each page
- [x] 4.2 Add `location /api/ { proxy_pass http://backend:8000/; }` to `frontend/nginx.conf`, forwarding uploads same-origin to the backend service; also add `absolute_redirect off;` so Nginx's directory trailing-slash redirects (e.g. `/ask` → `/ask/`) stay relative instead of pointing at Nginx's internal port 80, which broke navigation to `/ask` and `/feed/upload` when the container is published on a different host port (discovered during verification)

## 5. Frontend: home page (`/`)

- [x] 5.1 Update `frontend/public/index.html`: project description, brief plain-language explanation of RAG, visible "Beta" notice stating uploads aren't processed yet, and nav links to `/ask` and `/feed/upload`

## 6. Frontend: ask page (`/ask`)

- [x] 6.1 Create `frontend/public/ask/index.html` with nav and a bottom text input (non-functional — no `hx-post`/form action wired up)

## 7. Frontend: upload page (`/feed/upload`)

- [x] 7.1 Create `frontend/public/feed/upload/index.html` with nav, a file picker restricted to `.pdf` (`accept="application/pdf"`), and a submit control
- [x] 7.2 Wire the form to `POST /api/uploads` (via htmx `hx-post` + `hx-encoding="multipart/form-data"` or a plain HTML form) and display the success/error response inline

## 8. Verification

- [x] 8.1 `docker compose up --build`; confirm `/`, `/ask`, `/feed/upload` all load in a browser
- [x] 8.2 Upload a real PDF from `/feed/upload`; confirm success message and that the file appears in `backend/data/uploads/` on the host
- [x] 8.3 Attempt to upload a non-PDF file; confirm it is rejected with a clear error and nothing is written to storage
- [x] 8.4 Restart the backend service (`docker compose restart backend`); confirm the previously uploaded file still exists
- [x] 8.5 Confirm `/health` and `/docs` on the backend still work unchanged
