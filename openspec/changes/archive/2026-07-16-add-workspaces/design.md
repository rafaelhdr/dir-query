## Context

The app currently has exactly one implicit "workspace": a single shared
`UPLOAD_DIR` and a single llama-index `VectorStoreIndex` persisted under
`INDEX_DIR` (`backend/app/rag/index_service.py`). Both are process-global
state guarded by one `threading.Lock`. There is no database — nothing in
the stack today talks to Postgres, SQLAlchemy, or any migration tool.

This change introduces workspaces as the unit of isolation and moves chunk
storage from the llama-index on-disk index to Postgres + pgvector, per the
proposal. It touches the data layer, both backend routers, the Docker
Compose topology, and the static frontend's routing.

## Goals / Non-Goals

**Goals:**
- Isolate uploads, indexed chunks, and Q&A per workspace.
- Store chunks + embeddings in Postgres (pgvector) instead of the
  llama-index on-disk persisted index.
- Provide working migrations that run automatically on a single
  `docker compose up`, with no manual DB setup step.
- Keep the frontend a build-step-free static site served by Nginx.
- Keep the workspace password's hashing at rest, simple and quick.

**Non-Goals:**
- No login/session flow, no enforcement of the workspace password when
  viewing or using a workspace. The password is captured and hashed at
  creation only; access is by knowing the slug (same trust model the app
  already has today, just scoped). Enforcing it is explicit future work.
- No workspace rename/delete, no file listing/delete UI, no multi-user
  membership per workspace — a workspace has exactly one `owner_email` on
  record and no per-user roles.
- No re-indexing or backfill: there is no existing production data, so no
  data migration path is needed. Local filesystem `data/uploads` and
  `data/index` are deleted outright.
- No approximate nearest-neighbor (ANN) index (e.g. `ivfflat`/`hnsw`) on
  the embedding column yet — see Decisions.

## Decisions

### Chunks live in Postgres; PDF bytes stay on disk, scoped per workspace
`chunks` holds `chunk_index`, `text`, `embedding vector(384)`, and
`file_id` (FK to `files`) — no `workspace_id` column; a workspace's chunks
are found by joining `chunks.file_id -> files.id` and filtering on
`files.workspace_id`. Raw PDF bytes still live on a filesystem volume
(parsing needs the original file), but now under a per-workspace
subdirectory:
`UPLOAD_DIR/<workspace_id>/<stored_filename>`. The `files` table's
`filename` column holds that stored (sanitized/unique) name;
`original_name` holds the user's original filename. `vector(384)` matches
the existing `BAAI/bge-small-en-v1.5` HuggingFace embedding model already
in use — no embedding model change.

### Drop llama-index's storage/query-engine abstraction; keep it only for parsing + chunking
llama-index's `PGVectorStore` integration assumes its own schema (metadata
JSON blobs, its own ref-doc bookkeeping) that doesn't match the proposal's
explicit `chunks` table. Rather than fight that mismatch, `index_service.py`
keeps using llama-index's `PDFReader` (parsing) and `SentenceSplitter`
(chunking) but replaces `VectorStoreIndex` / `StorageContext` entirely with
hand-rolled steps:
1. Parse PDF → text nodes (llama-index `PDFReader` + `SentenceSplitter`).
2. Embed each node's text with the existing `HuggingFaceEmbedding`.
3. Insert one `chunks` row per node (`chunk_index`, `text`, `embedding`,
   `file_id`).
4. Update `files.status` to `indexed` (or `failed`).

Retrieval for `/ask` becomes: embed the question, run a raw SQL top-k query
joining `chunks` to `files` and filtering on `files.workspace_id`
(`SELECT chunks.* FROM chunks JOIN files ON chunks.file_id = files.id
WHERE files.workspace_id = :workspace_id ORDER BY chunks.embedding <=>
:query_embedding LIMIT k`), concatenate the retrieved chunk texts into a
prompt, and call the MiniMax LLM directly (`llama-index-llms-minimax`'s
`MiniMax` class still used for the completion call itself, just not
through an index-bound query engine).

**Alternative considered**: denormalize `workspace_id` directly onto
`chunks` to avoid the join. Rejected — `workspace_id` is fully derivable
from `chunks.file_id -> files.workspace_id`, so storing it twice only adds
a field that could drift if it were ever updated inconsistently, for no
real benefit: `files.workspace_id` and `chunks.file_id` are both indexed,
so the join stays cheap at this scale.

**Alternative considered**: adopt llama-index's `PGVectorStore` as-is and
drop the proposal's custom `chunks` shape. Rejected — the proposal is
explicit about the three-table schema, and that's a deliberate, reviewable
data model rather than an internal library implementation detail.

### SQLAlchemy (async) + Alembic for models and migrations
Adds `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, and `pgvector` (the
`pgvector-sqlalchemy` integration package, giving a `Vector(384)` column
type) as new backend dependencies. Alembic is the standard, well-understood
migration tool for this stack and keeps versioned SQL-generating migrations
in `backend/migrations/versions/`. The first migration creates the
`vector` and `pgcrypto` extensions and the three tables with the FKs and
indexes described below.

**Alternative considered**: a minimal hand-rolled SQL migration runner
(apply `.sql` files in order, tracked in a `schema_migrations` table).
Rejected as unnecessary — Alembic is one dependency and is the tool most
Python contributors already know, and it plays well with SQLAlchemy models
if the ORM is ever needed beyond raw SQL.

### Workspace password hashing via pgcrypto, not an app-side library
`crypt(:password, gen_salt('bf'))` (bcrypt via `pgcrypto`) is computed in
the `INSERT` statement itself; verification (for any future login flow)
would use `password = crypt(:input, password)`. This is Postgres' own
documented salted-password-hashing approach, needs no new Python
dependency, and matches "simple and quick." The first migration enables
`CREATE EXTENSION IF NOT EXISTS pgcrypto;` alongside `vector`.

### Slug generation with validation on collision
Slugs are derived at creation time: lowercase the name, replace runs of
non-alphanumeric characters with a single hyphen, trim leading/trailing
hyphens. `workspaces.slug` has a `UNIQUE` constraint; if the derived slug
already belongs to another workspace, creation is rejected with a 409
error telling the user the name is already taken and to choose another —
no automatic `-2`/`-3` suffixing. No user-editable slug field in this
change.

**Alternative considered**: auto-suffix on collision (`-2`, `-3`, ...).
Rejected — silently handing the user a different slug than the one implied
by their chosen name is surprising, and a clear rejection is simpler to
implement and reason about (a single `UNIQUE` constraint plus a 409
handler, no suffix-search loop).

### Frontend routing for `/w/<slug>/...` stays build-free
Nginx gets two new regex locations that rewrite any slug to one shared
static file, mirroring the existing SSI-partial pattern:
```
location ~ ^/w/[^/]+/ask/?$ { try_files /w/ask/index.html =404; }
location ~ ^/w/[^/]+/feed/upload/?$ { try_files /w/feed/upload/index.html =404; }
```
The page's own JS reads the slug from `window.location.pathname` and uses
it to build the API call path (`/api/w/<slug>/ask`, `/api/w/<slug>/uploads`).
This keeps one physical HTML file per page — no templating, no build step.

### Postgres service in Docker Compose
Add a `postgres` service using the official `pgvector/pgvector` image
tagged for the most recent Postgres major version (verify the current tag
at implementation time — `pg17`/`pg18` as available), a named volume for
data durability, and a healthcheck (`pg_isready`). The backend service
gets `depends_on: postgres: condition: service_healthy` and runs
`alembic upgrade head` before starting uvicorn (via the container's
command/entrypoint), so `docker compose up` alone provisions the schema on
a fresh volume.

### No ANN index on `embedding` yet
Given expected per-workspace chunk counts at this stage, an exact scan
(`ORDER BY embedding <=> ... LIMIT k`) with plain btree indexes on
`files.workspace_id` and `chunks.file_id` (supporting the join) is
sufficient and simpler to reason about than tuning `ivfflat`/`hnsw`
parameters prematurely. Revisit if retrieval latency becomes a problem.

## Risks / Trade-offs

- **[Risk]** Workspace URLs are reachable by anyone who knows the slug,
  with no password check yet. → **Mitigation**: explicitly called out as a
  non-goal in this change and in the proposal; slugs are not guessable
  sequential IDs, and enforcing the password is a natural, isolated
  follow-up change.
- **[Risk]** `pgcrypto`'s `crypt()`/blowfish (bcrypt) only hashes the first
  72 bytes of the input password — a generic bcrypt limitation, not
  specific to this implementation. Two passwords sharing the same first 72
  bytes would hash identically. → **Mitigation**: irrelevant in practice
  for realistic workspace passwords (far under 72 bytes); documented here
  rather than hidden.
- **[Risk]** Nginx regex-based routing for slug paths is a departure from
  the fully static, one-file-per-path pattern used elsewhere. →
  **Mitigation**: kept minimal (two `location` blocks), documented inline
  in `nginx.conf`, and consistent with the existing SSI-partial technique
  of serving shared markup via server-side rewriting.
- **[Risk]** Exact (non-ANN) vector search cost scales linearly with a
  workspace's chunk count. → **Mitigation**: acceptable at current scale;
  flagged as a revisit trigger above rather than solved preemptively.

## Migration Plan

There is no existing production data, so this ships as a single breaking
change rather than a staged rollout:
1. Add the `postgres` service and volume to `docker-compose.yml`; add DB
   env vars to `.env`/`.env.example`.
2. Add SQLAlchemy/Alembic/pgvector/asyncpg dependencies; add the first
   migration (extensions + `workspaces`, `files`, `chunks` tables +
   indexes).
3. Rewrite `index_service.py` per the Decisions above; update `uploads.py`
   and `ask.py` to be workspace-scoped; add `workspaces.py`.
4. Update frontend nav, add `/workspaces` and `/workspaces/new` pages, move
   `ask`/`feed/upload` pages under `/w/<slug>/...`, update `nginx.conf`.
5. Delete `backend/data/uploads`, `backend/data/index`, and the
   `HF_HOME`-adjacent llama-index storage code paths that are no longer
   reachable; remove the corresponding Compose volume mounts for the old
   directories (keep `HF_HOME` — the embedding model cache is unrelated to
   storage backend).
6. Rollback strategy: this is a pre-beta project with no real workspace
   data yet, so rollback is `git revert` + `docker compose down -v` to
   drop the Postgres volume; no forward-data-loss concern.

## Open Questions

- Exact `pgvector/pgvector` image tag to pin (depends on the most recent
  Postgres major version available for that image at implementation
  time).
- Whether/when to add workspace-password enforcement (a login/session
  flow) as a follow-up change.
