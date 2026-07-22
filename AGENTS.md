# AGENTS.md

Instructions for AI coding agents (and humans) working in this repository.

## Repository layout

This is a monorepo with a clear separation between backend and frontend:

```
.
├── backend/     # Python FastAPI API
├── frontend/    # Static htmx frontend, served by Nginx
├── openspec/    # Spec-driven change proposals (see below)
└── docker-compose.yml
```

- **`backend/`**: FastAPI application. Source lives in `backend/app/`, tests in
  `backend/tests/`. Dependencies are managed with [`uv`](https://docs.astral.sh/uv/)
  via `backend/pyproject.toml` and `backend/uv.lock`.
- **`frontend/`**: Plain HTML + [htmx](https://htmx.org) (vendored, not CDN-loaded),
  served as static files by Nginx. No build step, no framework.

The backend and frontend are independently deployable services connected only
by HTTP. Do not introduce cross-imports or shared code between them.

## Running locally

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (health check at `/health`)
- Backend interactive API docs: http://localhost:8000/docs (Swagger UI) and
  http://localhost:8000/redoc
- Frontend: http://localhost:8080

Copy `.env.example` to `.env` to override the exposed ports.

### Working across `wt` worktrees

Each worktree needs its own `.env`, `secrets/*.txt`, and (ideally) a warm
`backend/data/hf-cache/` to run `docker compose up`. `.config/wt.toml`'s
`post-start` hook runs `wt step copy-ignored` automatically whenever a new
worktree is created, copying these gitignored files/directories over from
the worktree it was branched from (scoped by `.worktreeinclude`) — so a
freshly created worktree can `docker compose up --build` immediately,
without manually recreating them.

Two things this does *not* do for you:

- **Postgres data starts fresh in every worktree.** `postgres`'s volume is
  bind-mounted to `./pg_data` (also copied by the hook) instead of a named
  Docker volume, but Postgres hardens its own data directory to `0700`
  under its container-internal user, so a plain file copy running as your
  host user can't actually read those bytes. In practice every new
  worktree gets an empty database — migrations run automatically on
  backend startup, so `docker compose up` still works, you just start
  with no users/workspaces.
- **Ports and `COMPOSE_PROJECT_NAME` are copied as-is.** Running more than
  one worktree's stack at the same time will collide on ports 8000/8080/
  5432 and on container/volume names. Before doing that, edit the new
  worktree's `.env`: bump `BACKEND_PORT`, `FRONTEND_PORT`, and
  `POSTGRES_PORT`, and set a unique `COMPOSE_PROJECT_NAME`.

### LLM and embedding providers

The embedding provider (used for indexing and retrieval) and the LLM
provider (used to answer questions) are each chosen independently via
environment variables:

- `EMBED_PROVIDER`: `cpu` (default — a local HuggingFace model, no API key
  needed) or `gemini` (Google's Gemini embeddings API, needs `GOOGLE_API_KEY`).
- `LLM_PROVIDER`: `minimax` (default) or `gemini` (needs `GOOGLE_API_KEY`).

An unrecognized value for either variable fails backend startup immediately
with a clear error. Uploading and indexing documents works with no
configuration at the default settings. Answering questions via `/ask` needs
a [MiniMax](https://www.minimax.io/) API key at the default `LLM_PROVIDER`.

Credentials are supplied the same way for both providers:

- **MiniMax** — **Recommended**: `cp secrets/minimax_api_key.txt.example
  secrets/minimax_api_key.txt` and put your real key in that file. It's
  gitignored — never commit it. **Fallback**: set `MINIMAX_API_KEY` in
  `.env` instead, if a secrets file isn't convenient (e.g. some CI setups).
- **Gemini** (needed if `EMBED_PROVIDER=gemini` and/or `LLM_PROVIDER=gemini`)
  — **Recommended**: `cp secrets/google_api_key.txt.example
  secrets/google_api_key.txt` and put your real
  [Google AI Studio](https://aistudio.google.com/) key in that file.
  **Fallback**: set `GOOGLE_API_KEY` in `.env` instead.

Without a required credential configured, uploads/indexing or `/ask` (as
applicable) return a clear configuration error instead of crashing the
backend.

### JWT signing key (user login)

Registration and login sign a JWT with `JWT_SECRET_KEY`, supplied the
same way as the LLM/embedding credentials above: **Recommended**:
`cp secrets/jwt_secret_key.txt.example secrets/jwt_secret_key.txt` and
put a long random string in that file. **Fallback**: set
`JWT_SECRET_KEY` in `.env` instead. Like the credentials above, a
missing key doesn't crash the backend — `/auth/register` and
`/auth/login` (and any endpoint that verifies a token) return a clear
configuration error instead.

### Workspace dedicated LLM key encryption

A workspace can be created with a dedicated LLM API key (Gemini or MiniMax)
instead of using the backend's shared credentials — see the
`workspace-llm-key-selection` capability. That key is encrypted before it's
stored, using `WORKSPACE_KEY_ENCRYPTION_SECRET`, supplied the same way as
the credentials above: **Recommended**: `cp
secrets/workspace_key_encryption_secret.txt.example
secrets/workspace_key_encryption_secret.txt` and put a long random string
in that file. **Fallback**: set `WORKSPACE_KEY_ENCRYPTION_SECRET` in `.env`
instead. This secret is intentionally separate from `JWT_SECRET_KEY` —
rotating one must not affect the other. If it's missing, creating a
workspace with a dedicated key returns a clear configuration error instead
of crashing the backend; losing or rotating it makes previously stored
dedicated keys permanently undecryptable.

`GEMINI_LLM_MODEL` (default `gemini-3-flash-preview`) and
`GEMINI_EMBED_MODEL` (default `gemini-embedding-001`) override the specific
Gemini models used, mirroring `MINIMAX_LLM_MODEL`. Google's currently
available models for new API keys shift over time (verified live: at the
time of writing, `gemini-2.5-flash`/`gemini-2.5-flash-lite` 404 for new
keys and `gemini-2.0-flash` hit a quota error, while the `-preview` model
above worked) — if the default stops working, override it with whatever
`client.models.list()` (via the `google-genai` SDK) shows as available and
working for your key.

#### Switching `EMBED_PROVIDER` on a deployment with existing indexed data

Different embedding providers produce vectors in incompatible vector
spaces (not just different dimensions) — switching `EMBED_PROVIDER` after
documents are already indexed requires clearing existing chunks and
re-indexing under the new provider. Run this once, right after changing
`EMBED_PROVIDER`:

```bash
docker compose exec backend uv run python scripts/reset_embeddings.py
```

This clears the `chunks` table, resizes its embedding column to match the
newly configured provider's actual output dimension, and marks affected
files back to `pending` — the next startup sync (or backend restart)
re-indexes them automatically under the new provider. **This is
destructive** (all existing chunks are cleared) and has no confirmation
prompt — only run it deliberately, after changing `EMBED_PROVIDER`.

## Backend development

```bash
cd backend
uv sync              # install dependencies into .venv
uv run pytest -v     # run tests
uv run uvicorn app.main:app --reload   # run locally without Docker
```

- Add new endpoints as an `APIRouter` in `backend/app/api/`, then register it
  in `backend/app/main.py`'s `create_app()`.
- Add a corresponding test module in `backend/tests/`.
- Keep `uv.lock` committed and in sync with `pyproject.toml` (`uv sync`
  regenerates it as needed).
- **Tests require a database whose name ends in `_test`** (e.g.
  `dir_query_test`), set via `POSTGRES_DB`. The suite's
  `conftest.py` truncates `workspaces`/`files`/`chunks` after every test and
  refuses to start if `POSTGRES_DB` doesn't end in `_test` — this guards
  against pointing the local `.env`'s dev `POSTGRES_DB` at pytest and wiping
  real data. Create it once with `CREATE DATABASE dir_query_test`
  on the same Postgres instance, run `POSTGRES_DB=dir_query_test
  uv run alembic upgrade head` to apply migrations to it, then run tests with
  that `POSTGRES_DB` set.

## Frontend development

The frontend is intentionally framework-free: static HTML files under
`frontend/public/`, using htmx for interactivity. When adding pages or
partials, keep them as plain HTML/htmx — do not introduce a JS build
toolchain without discussing it first.

Shared markup (the `<head>` boilerplate, nav, and page heading/beta-badge)
lives in `frontend/public/partials/` and is assembled at request time by
Nginx SSI (enabled via `ssi on;` in `frontend/nginx.conf`). New pages should
follow the existing pattern:

```html
<head>
  <!--#set var="page_title" value="My Page — Dir Query" -->
  <!--#include virtual="/partials/head.html" -->
</head>
<body>
  <!--#include virtual="/partials/nav.html" -->

  <!--#set var="page_heading" value="My Page" -->
  <!--#include virtual="/partials/heading.html" -->
  ...
```

`frontend/public/partials/` is marked `internal` in the Nginx config, so
those files can only be reached via SSI includes, not requested directly by
a browser. No build step is introduced — Nginx renders the includes on
every request, so the files on disk are exactly what gets served.

## Spec-driven changes with OpenSpec

This project uses [OpenSpec](openspec/) to plan and document non-trivial
changes before implementation. Before starting new feature work:

1. Check `openspec/specs/` for existing specs relevant to the area you're
   touching, and `openspec/changes/` for in-flight proposals.
2. For any change beyond a trivial fix, create a proposal first (see the
   `openspec-propose` / `opsx:propose` skill) rather than jumping straight to
   code.
3. Follow the existing OpenSpec skills (`opsx:apply`, `opsx:archive`,
   `opsx:sync`, `opsx:update`) to implement, sync, and archive changes.

This foundational setup (backend/frontend scaffolding, Docker Compose, CI-
ready tests) was created directly, without an OpenSpec change, since it
predates any specs. Everything from here on should go through the OpenSpec
workflow.

## Conventions

- Python: type-annotated, formatted per standard FastAPI idioms. Prefer small,
  focused `APIRouter`s over one large router file.
- API responses: define a Pydantic `BaseModel` in `backend/app/schemas.py` for
  every route's response shape and use it as the route's return-type
  annotation (FastAPI infers `response_model` from it), instead of returning
  a raw `dict`. This gets response validation/filtering and an accurate
  OpenAPI schema in `/docs` for free. Build the model with explicit keyword
  arguments from named ORM attributes (never `model_validate`/
  `from_attributes` on the ORM object directly) so fields that must never be
  exposed (e.g. a workspace's `owner_user_id`) can't leak just because a new
  column gets added to the model later.
- Tests: one test module per API router/feature area, using the `TestClient`
  fixture in `backend/tests/conftest.py`.
- No database, auth, or background workers are set up yet — introduce them
  only when a concrete task requires them, and document the decision via
  OpenSpec.
