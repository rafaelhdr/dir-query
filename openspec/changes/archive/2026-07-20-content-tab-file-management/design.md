## Context

The workspace feed today has only a write-only upload form
(`frontend/public/w/feed/upload/index.html`, backed by
`POST /api/w/{slug}/uploads` in `app/api/uploads.py`). Files are rows in
the `files` table (`id`, `workspace_id`, `filename` (stored, UUID-prefixed),
`original_name`, `status`, `uploaded_at`), with `chunks` already
`ON DELETE CASCADE` from `files.id`. There's no endpoint to list, open, or
delete a file, and no uniqueness constraint on `original_name`. This design
covers turning that into a full content-management surface: rename the tab,
add a collapsible add-content form with an editable name, validate
duplicate names, and add list/open/delete with a manual refresh.

**Post-implementation refinement (same change, still unarchived):** once
this shipped, user feedback split what had been a single `original_name`
field into two distinct, independently-unique concerns — a user-editable
**display name** (e.g. "History") and the uploaded file's own **original
filename** (e.g. `history.pdf`) — and moved the "open" affordance from a
separate button onto the file's name itself. The sections below reflect
this split; where a decision changed, the original rationale is kept for
context and the revision is called out explicitly.

## Goals / Non-Goals

**Goals:**
- Rename the "Upload" tab/page to "Content" (`/w/<slug>/feed/files`).
- Let the user set a display name for an uploaded file (defaulting to the
  picked file's filename), rejecting names that collide within the
  workspace.
- Track the display name and the file's original filename as two separate
  fields, each independently unique per workspace.
- List all files in a workspace with display name (clickable to open, with
  an icon indicating it opens in a new tab), original filename, status, and
  delete action; a manual refresh button reloads the list from the
  database.
- Deleting a file removes it from the filesystem, the `files` row, and
  (via existing FK cascade) its `chunks`.
- Shape the list response for future pagination without implementing it.

**Non-Goals:**
- No pagination, infinite scroll, or `next`/`total` values yet — only the
  envelope shape.
- No renaming of an already-uploaded file after the fact.
- No background polling/auto-refresh; refresh is manual only.
- No change to indexing behavior, embedding providers, or the ask flow.

## Decisions

**Route rename, no compatibility redirect.**
`/w/<slug>/feed/upload` becomes `/w/<slug>/feed/files` in both the
static file layout and `nginx.conf`. The project has no external users
depending on the old URL yet, so a redirect/alias would be pure overhead.
Alternative considered: keep `/feed/upload` as the path and only rename
the tab label — rejected because the proposal explicitly renames the
tab, and an inconsistent path-vs-label would read like a leftover.

**Display name and original filename are two separate fields, each independently unique per workspace (revised).**
The frontend already has the picked file's `filename` available before
submit; it prefills a `name` text input the user can edit. The name is
sent as its own form field (alongside `file`) in the same
`POST /api/w/{slug}/uploads` request — no new upload endpoint. The
`files` table's former single `original_name` column is split into two:
`display_name` (from the `name` form field, falling back to the picked
file's filename only if the field is empty) and `original_filename` (the
picked file's filename as reported by the browser, always — this is not
user-editable). Each gets its own unique index scoped to the workspace:
`(workspace_id, display_name)` and `(workspace_id, original_filename)`.
Two people can upload files both literally named `report.pdf` from their
local disks as long as they choose different display names — but neither
field alone may collide with an existing file in the same workspace.

Validation is now check-then-insert *with* a DB-constraint fallback,
rather than relying on the constraint alone: the endpoint queries for an
existing `display_name` match and an existing `original_filename` match
before inserting, so it can return a message naming which field
conflicted (e.g. "a file named 'History' already exists" vs. "a file with
filename 'history.pdf' already exists"). The unique indexes remain the
source of truth for correctness — inserting still catches `IntegrityError`
as a fallback with a generic conflict message, so a race between two
concurrent uploads is still rejected even if both pass the pre-check,
just without naming which field collided (rare enough in practice not to
warrant parsing the constraint name out of the driver exception). This
mirrors the existing
workspace-name-conflict pattern in `app/api/workspaces.py`, extended with
the pre-check purely for clearer error messages.
Alternative considered: rely on the DB constraint alone (original design)
— rejected because with two independently-unique fields, the constraint
name is the only way to know which one collided, and parsing it out of a
race-only exception path for the *common* case (no race) is worse UX than
just checking first. Alternative considered: single generic "a conflicting
file exists" message regardless of which field collided — rejected as
needlessly vague when the pre-check already knows which field it was.

**New `document-management` capability owns list/delete; opening is a URL, not an endpoint.**
Two new routes, added in a new `app/api/files.py` router:
- `GET /api/w/{slug}/files` → `{"data": [{"id", "display_name",
  "original_filename", "status", "uploaded_at", "url"}, ...]}` (field
  names updated from the single `original_name` per the display-name /
  original-filename split above). The `data` envelope leaves room for
  `next`/`total` later without a breaking shape change. `url` is built
  from the same `workspace_id`/stored-`filename` pair already used for
  on-disk storage (e.g. `/files/{workspace_id}/{filename}`) — it is not a
  backend endpoint, it's the path nginx serves that file at directly (see
  below).
- `DELETE /api/w/{slug}/files/{file_id}` → deletes the row (the DB
  cascades to `chunks`), then removes the file from disk. Delete the DB
  row first inside the transaction; only unlink from disk after commit
  succeeds, so a filesystem error can't leave an orphaned DB row pointing
  at a deleted file, and a DB error leaves the file+row both still
  present (safe to retry).
Alternative considered: keep these routes in `uploads.py` — rejected,
since that file is scoped to the single write path and mixing in
list/delete concerns would blur its purpose; a sibling `files.py` keeps
each router single-purpose.

**Files are served directly by nginx as static assets, not proxied through the backend.**
`nginx.conf` gains a `location /files/ { alias /data/uploads/; }` block
(exact path TBD at implementation time to match `UPLOAD_DIR`'s on-disk
layout), and `docker-compose.yml` mounts the same host uploads directory
(`./backend/data/uploads`) into the `frontend` service, read-only, at
that alias target. The list endpoint's `url` field is just this static
path — the frontend renders each file's display name itself as an `<a
target="_blank">` href pointing at `url` (with a small icon indicating it
opens in a new tab), rather than a separate "Open" button/column, per
follow-up feedback. No fetch+blob juggling, no bytes passing through the
FastAPI process. This also keeps the response shape future-proof: swapping
local storage for something like S3 later only means changing what `url`
resolves to (e.g. a signed S3 URL) — the field stays a plain URL string,
no client-side change required.
Alternative considered: a `GET .../files/{file_id}/content` endpoint that
streams the PDF through FastAPI — this was the original design, but it
adds unnecessary proxying through the app process for what is fundamentally
a static asset, and bakes the assumption that "opening a file" always
means "asking this specific API" into the response shape rather than
just handing back a URL.

**Frontend structure: `<details>`/`<summary>` for the collapsible section,
plain fetch calls for list/delete, no new build tooling.**
Consistent with the rest of the frontend (plain htmx + vanilla JS, no
framework, no build step). The add-content form lives inside a
`<details>` element; submit handler clears the form and re-triggers the
same list-fetch function used by the refresh button and the initial page
load.

## Risks / Trade-offs

- [Old bookmarks/links to `/feed/upload` 404] → Acceptable: pre-launch
  project, no external users depend on the old path yet.
- [Unique constraint migration on existing data] → Existing rows are
  expected to have no duplicate `(workspace_id, original_name)` pairs
  today (upload is the only entry point so far); the migration adds the
  constraint directly. If it ever fails on real data, the fix is a
  one-off dedup migration, not a design change.
- [Backfilling `original_filename` for rows created before the split] →
  Every existing row's `original_name` was, at the time it was written,
  literally the uploaded file's own filename (the display-name/original-
  filename distinction didn't exist yet), so the migration backfills
  `original_filename` from the pre-split `original_name` value for
  existing rows before renaming that column to `display_name`. No data is
  invented; the backfilled value is exactly what the original upload
  request's filename was.
- [Deleting the DB row before the disk file] → If the process crashes
  between commit and unlink, a file is orphaned on disk with no DB
  reference. Mitigation: acceptable for now (orphaned disk space, not a
  correctness or data-exposure issue); a future cleanup job could sweep
  unreferenced files if this becomes a problem.
- [Directly exposing the uploads directory via nginx] → Stored filenames
  are UUID-prefixed (`{uuid}-{sanitized original name}`), so paths are not
  guessable/enumerable; the `alias` block serves only exact existing
  files with no directory listing enabled. Acceptable exposure for
  non-sensitive PDFs at current scale; revisit with signed URLs if
  workspace content ever needs access control beyond the workspace
  password.
- [nginx and the backend must agree on the uploads directory layout] →
  Both derive the `{workspace_id}/{filename}` layout from the same
  `UPLOAD_DIR`-configured volume already mounted into the backend; the
  nginx `alias` and the `url` field built by the list endpoint are two
  views onto that one convention, not duplicated logic.

## Migration Plan

1. Add the `(workspace_id, original_name)` unique index via an Alembic
   migration.
2. Ship the backend routes (name field + validation on upload, list with
   `url`, delete) behind no flag — additive except for the rename.
3. Add the nginx static `/files/` location and the `docker-compose.yml`
   uploads-directory mount for the `frontend` service.
4. Ship the frontend rename + new UI in the same change (moving
   `w/feed/upload` → `w/feed/files`, updating `nginx.conf`'s tab route).
5. No rollback complexity beyond a normal revert: the migration only adds
   a constraint (safe to drop), and no destructive data changes occur.
6. (Follow-up) Add a second migration: add `original_filename` (backfilled
   from `original_name`, then set `NOT NULL`), rename `original_name` to
   `display_name`, drop the old combined unique index, and create the two
   new per-field unique indexes.
7. Ship the backend changes (two-field validation, updated list response)
   and the frontend changes (name-as-open-link with icon, new "original
   filename" column) together, since the response shape change is
   breaking for any client relying on the old `original_name` key.

## Open Questions

- None outstanding — small enough scope that the decisions above resolve
  the ambiguity called out in the proposal.
