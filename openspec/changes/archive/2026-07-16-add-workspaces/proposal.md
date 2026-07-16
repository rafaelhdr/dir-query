## Why

Today the whole application is a single shared document pool: every upload
goes into one filesystem folder and every question is answered against one
combined index. There is no way for different people or companies to keep
their documents and questions separate. Workspaces introduce that
separation, and moving chunk storage into Postgres (with pgvector) replaces
the ad hoc on-disk llama-index persistence with a queryable, per-workspace
store that scales past a single tenant.

## What Changes

- Add a `workspaces` table (`id`, `name`, `slug`, `owner_email`, `password`,
  `created_at`) and a page at `/workspaces/new` to create one. Slugs are
  derived from the name (e.g. "Company X" → `company-x`); if that slug is
  already taken, creation is rejected with a clear error asking the user
  to choose a different name, rather than silently making up a variant.
- Add a `/workspaces` listing page, reachable from the header nav, showing
  existing workspaces and a link to create a new one.
- **BREAKING**: Replace the header nav's `/ask` and `/feed/upload` links
  with `/home` and `/workspaces`. The root path `/` becomes an alias that
  serves the same home content.
- **BREAKING**: Move the ask and upload pages under a workspace path prefix:
  `/w/<slug>/ask` and `/w/<slug>/feed/upload`. The old unscoped `/ask` and
  `/feed/upload` routes are removed.
- **BREAKING**: Replace the llama-index persisted index directory with
  Postgres tables: `files` (one row per uploaded PDF, tracking its
  filesystem path and `status`: pending/indexed/failed) and `chunks` (one
  row per text chunk, with a pgvector `embedding vector(384)` column
  matching the existing `BAAI/bge-small-en-v1.5` embedding model's output
  size). `chunks` references its owning file via `file_id`; a workspace's
  chunks are found by joining through `files` (`chunks.file_id ->
  files.id -> files.workspace_id`) rather than storing `workspace_id`
  redundantly on `chunks`. PDF files themselves keep living on the
  filesystem, now under a per-workspace directory — only the AI-facing
  state (index/chunks/embeddings and file metadata) moves into Postgres.
- Add a Postgres service (latest major version, with the `pgvector`
  extension) to `docker-compose.yml`, plus a backend migrations setup that
  runs automatically on startup so a single `docker compose up` provisions
  the schema.
- Add `POSTGRES_PASSWORD` (and related connection settings) to `.env`;
  `.env.example` ships a placeholder (`CHANGEME`).
- Workspace passwords are hashed with `pgcrypto`'s `crypt()` +
  `gen_salt('bf')` (Postgres' documented approach for salted password
  hashes) at creation time. Enforcing the password to *access* a workspace
  (a login/session flow) is explicitly out of scope for this change — only
  hashed storage at creation time is included.
- Remove the now-unused filesystem upload/index directories and the
  llama-index on-disk persistence code path.

## Capabilities

### New Capabilities
- `workspace-management`: creating a workspace (name → slug, owner email,
  hashed password) and listing existing workspaces, via `/workspaces` and
  `/workspaces/new`.

### Modified Capabilities
- `document-upload`: uploads move from `/feed/upload` to
  `/w/<slug>/feed/upload`, are scoped to a workspace, and are persisted as
  rows in the Postgres `files` table (plus the underlying PDF bytes on
  disk, keyed by workspace) instead of a flat shared upload directory.
- `document-indexing`: chunk storage and embeddings move from the
  llama-index on-disk persisted index to the Postgres `chunks` table
  (pgvector), scoped per workspace; a file's indexing state is tracked via
  the `files.status` column instead of implicit index membership.
- `question-answering`: retrieval is scoped to a single workspace's chunks
  (via a join through `files`) instead of a single global index; the
  endpoint moves to `/w/<slug>/ask`.
- `ask-page`: page moves from `/ask` to `/w/<slug>/ask` and is only
  reachable from within a workspace; nav links updated accordingly.
- `home-page`: nav links change from `/ask` / `/feed/upload` to `/home` /
  `/workspaces`; the page explains workspaces as the way to separate
  document groups.

## Impact

- **Backend**: new `app/db/` (connection/session setup) and
  `app/models/` (or equivalent) for `workspaces`, `files`, `chunks`; new
  migrations directory; `app/rag/index_service.py` rewritten to read/write
  Postgres instead of llama-index's on-disk `StorageContext`; `uploads.py`
  and `ask.py` routers become workspace-scoped (path parameter, workspace
  lookup); new `workspaces.py` router.
- **Frontend**: new `/workspaces/index.html` and `/workspaces/new/index.html`
  pages; `/ask` and `/feed/upload` pages move under `/w/<slug>/...` (Nginx
  routing/templating implications since these are static files with no
  build step — addressed in design.md); nav partial updated; `/home` added
  as an explicit path alongside `/`.
- **Infra**: `docker-compose.yml` gains a `postgres` service and a named
  volume; `.env` / `.env.example` gain DB connection variables; backend
  gains a Postgres client dependency and a migration tool dependency.
- **Data migration**: none — there is no existing production data to
  migrate; existing local `data/uploads` and `data/index` directories are
  deleted as part of this change.
