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

### MiniMax API key (needed for `/ask`)

Uploading and indexing documents works with no configuration. Answering
questions via `/ask` needs a [MiniMax](https://www.minimax.io/) API key:

- **Recommended**: `cp secrets/minimax_api_key.txt.example secrets/minimax_api_key.txt`
  and put your real key in that file. It's gitignored — never commit it.
- **Fallback**: set `MINIMAX_API_KEY` in `.env` instead, if a secrets file
  isn't convenient (e.g. some CI setups).

Without either, uploads and indexing still work; `/ask` returns a clear
configuration error instead of an answer.

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
  <!--#set var="page_title" value="My Page — Understand Your Stuffs" -->
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
- Tests: one test module per API router/feature area, using the `TestClient`
  fixture in `backend/tests/conftest.py`.
- No database, auth, or background workers are set up yet — introduce them
  only when a concrete task requires them, and document the decision via
  OpenSpec.
