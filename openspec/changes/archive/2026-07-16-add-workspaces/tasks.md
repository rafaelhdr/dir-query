## 1. Postgres infrastructure

- [x] 1.1 Add a `postgres` service to `docker-compose.yml` using the
      `pgvector/pgvector` image tagged for the most recent Postgres major
      version, with a named volume for data durability and a
      `pg_isready` healthcheck.
- [x] 1.2 Add `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
      `POSTGRES_HOST`, `POSTGRES_PORT` (and a derived `DATABASE_URL`) to
      `.env` and `.env.example` (`.env.example` uses `CHANGEME` for the
      password).
- [x] 1.3 Wire the `backend` service's `depends_on` to
      `postgres: condition: service_healthy` and pass the DB env vars
      through.

## 2. Backend dependencies and DB layer

- [x] 2.1 Add `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, and
      `pgvector` (the SQLAlchemy `Vector` type integration) to
      `backend/pyproject.toml`; run `uv sync`.
- [x] 2.2 Add `app/db/session.py` (async engine + session factory built
      from the DB env vars) and `app/db/models.py` (`Workspace`, `File`,
      `Chunk` SQLAlchemy models matching the proposal's schema; `Chunk`
      has no `workspace_id` column — its workspace is resolved via
      `Chunk.file_id -> File.workspace_id`).
- [x] 2.3 Initialize Alembic under `backend/migrations/`, configured to
      read the same DB env vars as the app.
- [x] 2.4 Write the first migration: `CREATE EXTENSION IF NOT EXISTS
      vector;`, `CREATE EXTENSION IF NOT EXISTS pgcrypto;`, and the
      `workspaces`, `files`, `chunks` tables with their FKs, a `UNIQUE`
      constraint on `workspaces.slug`, the `files.status` check/enum
      (`pending`/`indexed`/`failed`), and btree indexes on
      `files.workspace_id` and `chunks.file_id`.
- [x] 2.5 Update the backend Docker image/command so `alembic upgrade
      head` runs automatically before `uvicorn` starts, so a single
      `docker compose up` provisions the schema on a fresh volume.

## 3. Workspace management

- [x] 3.1 Add `app/api/workspaces.py`: `POST /workspaces` (creates a
      workspace — derives a slug from `name`, hashes `password` via
      `crypt(:password, gen_salt('bf'))` in the insert, stores
      `owner_email`; returns 409 with a clear message if the slug is
      already taken) and `GET /workspaces` (lists existing workspaces)
      and `GET /workspaces/{slug}` (fetch one, 404 if missing).
- [x] 3.2 Register the workspaces router in `app/main.py`.
- [x] 3.3 Add a small slug-generation helper (lowercase, non-alphanumeric
      runs → single hyphen, trim edges — no collision suffixing) with
      unit tests; collision detection itself happens at the DB layer via
      the `workspaces.slug` `UNIQUE` constraint, caught and turned into
      the 409 response.
- [x] 3.4 Add `backend/tests/test_workspaces.py` covering: create,
      duplicate name rejected with 409, missing-field validation, list
      (empty and non-empty), password not present in the create
      response, get-by-slug 404.

## 4. Rewrite indexing/retrieval for Postgres

- [x] 4.1 Add a workspace lookup dependency (by slug, 404 if missing)
      shared by the uploads and ask routers.
- [x] 4.2 Rewrite `app/rag/index_service.py`: drop
      `StorageContext`/`VectorStoreIndex`/`load_index_from_storage`;
      keep `PDFReader` + a `SentenceSplitter` for chunking; add
      `index_uploaded_file(file_id, path)` that parses, chunks, embeds
      (existing `HuggingFaceEmbedding`), inserts `chunks` rows (each
      tagged with `file_id` only — no `workspace_id`), and updates
      `files.status`.
- [x] 4.3 Add `sync_pending_files()` (replaces `sync_index()`): on
      startup, query `files` with `status = 'pending'` across all
      workspaces, index each, logging counts as today (found / already
      indexed / newly indexed) plus per-file outcome; catch and log
      per-file failures (setting `status = 'failed'`) without raising.
- [x] 4.4 Add `answer_question(workspace_id, question)`: embed the
      question, run a top-k query joining `chunks` to `files` and
      filtering on `files.workspace_id`
      (`... JOIN files ON chunks.file_id = files.id WHERE
      files.workspace_id = :workspace_id ORDER BY chunks.embedding <=> :q
      LIMIT k`), build a prompt from the retrieved chunk texts, call the
      MiniMax LLM directly for the completion, and return the answer plus
      the distinct source filenames.
- [x] 4.5 Update `app/main.py`'s lifespan to call `sync_pending_files()`
      instead of `sync_index()`.

## 5. Workspace-scoped upload and ask endpoints

- [x] 5.1 Move `app/api/uploads.py`'s route to
      `POST /w/{slug}/uploads`: look up the workspace (404 if missing),
      store the file under `UPLOAD_DIR/<workspace_id>/`, insert a
      `files` row (`status='pending'`), and background-task
      `index_service.index_uploaded_file(file_id, path)`.
- [x] 5.2 Move `app/api/ask.py`'s route to `POST /w/{slug}/ask`: look up
      the workspace (404 if missing) and call
      `index_service.answer_question(workspace_id, question)`.
- [x] 5.3 Update `backend/tests/test_uploads.py` and
      `backend/tests/test_ask.py` for the new workspace-scoped routes
      and Postgres-backed behavior (using a test DB/fixtures per
      `backend/tests/conftest.py`).

## 6. Frontend: workspaces pages and nav

- [x] 6.1 Add `frontend/public/workspaces/index.html` (lists workspaces
      via `hx-get`/JS against `/api/workspaces`, links to each
      workspace's ask page, links to `/workspaces/new`).
- [x] 6.2 Add `frontend/public/workspaces/new/index.html` (form for name,
      owner email, password; `hx-post` to `/api/workspaces`; redirects
      into the new workspace on success).
- [x] 6.3 Add `frontend/public/home/index.html` mirroring the current
      `frontend/public/index.html` content, updated to explain
      workspaces; update `frontend/public/index.html` to the same
      content so `/` and `/home` match.
- [x] 6.4 Update `frontend/public/partials/nav.html`: replace the `/ask`
      and `/feed/upload` links with `/home` and `/workspaces`.

## 7. Frontend: move ask/upload under /w/<slug>/

- [x] 7.1 Add `frontend/public/w/ask/index.html` (moved from
      `frontend/public/ask/index.html`): read the slug from
      `window.location.pathname`, post to `/api/w/<slug>/ask`, link back
      to `/home` and `/w/<slug>/feed/upload`.
- [x] 7.2 Add `frontend/public/w/feed/upload/index.html` (moved from
      `frontend/public/feed/upload/index.html`): read the slug from the
      URL, post to `/api/w/<slug>/uploads`.
- [x] 7.3 Delete the old `frontend/public/ask/` and
      `frontend/public/feed/` directories.
- [x] 7.4 Update `frontend/nginx.conf` with the two regex locations that
      route `/w/<slug>/ask` and `/w/<slug>/feed/upload` to the shared
      static files above, keeping `/api/` proxying and the internal
      `/partials/` rule intact.

## 8. Cleanup

- [x] 8.1 Remove `backend/data/index` from `docker-compose.yml` volume
      mounts (no longer used now that the index lives in Postgres); keep
      `backend/data/uploads` (PDFs still persist on the filesystem per
      the design's decision to keep raw files on disk) and
      `backend/data/hf-cache` (embedding model cache).
- [x] 8.2 Delete the `INDEX_DIR` setting from `app/config.py` (no longer
      used) and add the Postgres connection settings there instead;
      remove now-unused llama-index storage imports.
- [x] 8.3 Delete any now-empty local `backend/data/uploads` /
      `backend/data/index` directories from the repo/gitignore if
      tracked.

## 9. Verification

- [x] 9.1 `docker compose up --build` from a clean state (no existing
      Postgres volume) provisions the schema automatically in one run.
- [x] 9.2 Manually walk through: create a workspace at `/workspaces/new`
      → upload a PDF at its `/w/<slug>/feed/upload` → ask a question at
      its `/w/<slug>/ask` → confirm a second, unrelated workspace cannot
      see the first workspace's content.
- [x] 9.3 `uv run pytest -v` passes in `backend/`.
