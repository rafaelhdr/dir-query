## Context

The repo is a fresh monorepo: a FastAPI backend (`backend/`) exposing only `GET /health`, and a static-HTML + htmx frontend (`frontend/`) served by Nginx, currently a single "Hello world" page. Per `AGENTS.md`, the frontend is intentionally framework-free (no JS build toolchain) and the backend/frontend communicate only over HTTP as independently deployable services. This change adds the first three real pages and the first backend capability beyond health checks: accepting PDF uploads.

## Goals / Non-Goals

**Goals:**
- Serve three static pages (`/`, `/ask`, `/feed/upload`) from the existing Nginx-based frontend, no build step.
- Let a user upload a PDF from `/feed/upload` and have it durably stored by the backend, surviving container restarts, in a location easy to find and inspect on the host.
- Keep the browser-facing surface same-origin so the frontend never needs CORS configuration.
- Make "beta" status and the upload-only (no processing yet) nature obvious on the home page.

**Non-Goals:**
- No RAG/Q&A logic behind `/ask` — the input box exists but submits nowhere.
- No PDF parsing, text extraction, chunking, or indexing of uploaded files.
- No CRUD on uploads: no listing, download, rename, or delete endpoints.
- No authentication/authorization.
- No deep file validation (e.g., magic-byte sniffing, virus scanning) — extension + declared content-type checks only.
- No database records for uploads — files are just written to disk in this change.

## Decisions

### 1. Pages are plain static files, routed by Nginx directory structure
Each page is `frontend/public/<route>/index.html` (home stays at `frontend/public/index.html`). Nginx's existing `try_files $uri $uri/ =404;` + `index index.html;` already resolves `/ask` → `/ask/index.html` and `/feed/upload` → `/feed/upload/index.html`.

Nginx issues a `301` from `/ask` to `/ask/` (its standard directory-trailing-slash behavior) before serving the index file. By default that redirect's `Location` header is an absolute URL built from Nginx's own `listen` port (80), not the host port Compose publishes it on (`8080`) — so following the redirect from outside the container hits nothing. Fixed with `absolute_redirect off;` in `frontend/nginx.conf`, which makes Nginx emit a relative `Location: /ask/` instead, so the browser keeps whatever host/port it already used.
- **Alternative considered**: server-side templating (Jinja2 via a Python service). Rejected — already decided against in the foundation change; three static pages don't justify introducing a templating engine.

### 2. Shared navigation is duplicated markup, not a fetched partial
A small `<nav>` snippet (3 links) is copied into each of the three HTML files rather than loaded via `hx-get` from a shared partial.
- **Alternative considered**: htmx `hx-get`-loaded nav partial (`/partials/nav.html`) with `hx-trigger="load"`. Rejected for now — adds a network round-trip and a flash-of-missing-nav for a 3-line, 3-page site. Revisit if the page count grows enough that duplication becomes a real maintenance cost.

### 3. Nginx reverse-proxies `/api/` to the backend; browser never calls the backend origin directly
Add an Nginx `location /api/ { proxy_pass http://backend:8000/; }` block (using the Compose service name `backend` for DNS resolution inside the Compose network). The upload form on `/feed/upload` posts to `/api/uploads`, same-origin from the browser's perspective.
- **Alternative considered**: CORS on the FastAPI app (`CORSMiddleware`) allowing `http://localhost:8080`. Rejected — same-origin via proxy is simpler for the browser, avoids preflight requests, and keeps the backend's published host port (`8000`) purely a developer convenience (docs/health) rather than a required public surface. The backend keeps its own `/health`, `/docs` etc. reachable directly for development.

### 4. Backend upload endpoint: `POST /uploads`, multipart/form-data, single `file` field
- Router: `backend/app/api/uploads.py`, registered in `create_app()` alongside `health`.
- Validation: reject if filename doesn't end in `.pdf` (case-insensitive) or declared `content-type` isn't `application/pdf`. Reject if size exceeds a configurable max (`MAX_UPLOAD_BYTES`, default 20 MB) → `413`.
- Storage: files are written to `UPLOAD_DIR` (env var, default `/data/uploads` inside the container). To avoid collisions and path traversal, the stored filename is `<uuid4>-<sanitized-original-name>` — the original name is kept (stripped of path separators) purely for human readability; the UUID prefix guarantees uniqueness and the sanitization prevents directory traversal via crafted filenames.
- Response: `201` with `{"filename": "<stored-name>", "original_filename": "<name>", "size": <bytes>}`.
- **Alternative considered**: streaming hash-based dedup or a DB row per upload. Rejected as out of scope — no processing pipeline exists yet to need it; flat-file storage is sufficient for a beta that only accepts uploads.

### 5. Storage is a bind mount to a repo-local folder
`docker-compose.yml` mounts a repo-local folder (`./backend/data/uploads`) into the `backend` service at `UPLOAD_DIR` (`/data/uploads`). Uploaded files land directly in that folder on the host, visible with a normal file browser/`ls` — no `docker exec` needed to inspect them, and no volume to know about. This is the easiest option for someone cloning the repo to poke at uploaded files locally. The folder is `.gitignore`d (with a `.gitkeep` so the empty directory still exists after clone) so uploaded PDFs are never accidentally committed.
- **Alternative considered**: a Docker Compose named volume (e.g., `uploads_data`). Rejected as the default — it hides uploaded files inside Docker's storage area, requiring `docker compose exec backend ls ...` or `docker volume inspect` just to see what was uploaded, which adds friction for anyone testing this locally by copy-pasting files in.

### 6. Home page content
Static copy explaining: (a) what this project is, (b) a short, plain-language explanation of RAG (Retrieval-Augmented Generation) — "a way of answering questions by first retrieving relevant pieces of your own documents, then giving them to a language model to generate an answer" — and (c) a visible "Beta" badge/notice stating uploads are accepted but not yet processed or searchable.

## Risks / Trade-offs

- **[Risk]** Duplicated nav markup drifts across 3 files as pages are edited. → **Mitigation**: nav is tiny (3 links); revisit shared-partial approach (Decision 2) once a 4th page is added.
- **[Risk]** Extension/content-type validation is spoofable (a non-PDF renamed to `.pdf` with a forged content-type header passes). → **Mitigation**: explicitly a non-goal for this beta (see Non-Goals); acceptable since uploaded files are not yet parsed or executed. Flag as an open question for a follow-up change once processing is added.
- **[Risk]** A repo-local bind mount folder must exist before Compose starts, and could theoretically be committed by accident. → **Mitigation**: `.gitignore` excludes its contents (with a `.gitkeep` placeholder committed so the folder itself is present after clone).
- **[Risk]** Nginx proxy_pass to `http://backend:8000/` only resolves inside the Compose network — running frontend/backend outside Compose (e.g., `uvicorn --reload` directly) breaks the proxy. → **Mitigation**: out of scope; Compose is the documented local-dev path per `AGENTS.md`.

## Migration Plan

No data migration (net-new feature). Deployment is just building and starting the updated `frontend` and `backend` images/services via `docker compose up --build`. Rollback is reverting the change (previous images still work; the new bind-mounted folder is additive and harmless if unused).

## Open Questions

- Should uploads eventually get a DB record (filename, upload time, status) once a processing pipeline exists? Deferred to a future change.
- Should the max upload size and allowed types be surfaced in the UI before the user picks a file, or only enforced server-side (current plan)? Current plan is server-side only with a clear error message; revisit if UX feedback warrants client-side hints.
