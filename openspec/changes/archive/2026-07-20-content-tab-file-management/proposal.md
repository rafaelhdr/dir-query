## Why

Today the "Upload" tab is write-only: a user can push a PDF but has no way
to see what's already in the workspace, confirm indexing finished, open a
previously uploaded file, or remove one they no longer want. As workspaces
accumulate documents, this makes the feed opaque and impossible to clean up.

## What Changes

- Rename the "Upload" tab to "Content" (`/w/<slug>/feed/files`, replacing
  `/w/<slug>/feed/upload`). **BREAKING**: the old upload URL no longer
  resolves.
- Turn the existing upload form into a collapsible "Add content" section.
  Selecting a file autofills an editable name field with the file's
  filename; submitting sends that name alongside the file.
- Reject uploads whose chosen name already exists in the workspace with a
  clear error, instead of silently allowing duplicate names.
- On successful upload, clear the add-content fields and refresh the file
  list automatically.
- Add a file list below the add-content section showing every file's name,
  status, an "Open" button (opens the file in a new tab), and a "Delete"
  button, plus a manual refresh button above the list.
- Add a paginate-ready `GET` list endpoint (`{"data": [...]}` envelope,
  leaving room for future `next`/`total` fields) where each file entry
  includes a URL for opening it directly — served today by nginx straight
  from local storage (no streaming through the backend), swappable later
  for something like an S3 URL without changing the response shape — and
  a `DELETE` endpoint that removes the file from disk and the database,
  cascading to its chunks.

## Capabilities

### New Capabilities
- `document-management`: listing, opening, and deleting previously
  uploaded files for a workspace, including the paginate-ready list
  response envelope and filesystem+database+chunk cleanup on delete.

### Modified Capabilities
- `document-upload`: the page moves from `/w/<slug>/feed/upload` to
  `/w/<slug>/feed/files`, the tab label changes from "Upload" to
  "Content", the upload form becomes a collapsible section with an
  editable, autofilled name field, duplicate names within a workspace are
  now rejected, and the "write-only, no CRUD" and "no listing capability"
  requirements are removed since `document-management` now supersedes them.

## Impact

- Backend: `app/api/uploads.py` (name field + duplicate-name validation),
  new `app/api/files.py`-style routes for list (including each file's
  opening URL) and delete, `app/db/models.py` (uniqueness constraint on
  `(workspace_id, original_name)`), a migration for that constraint.
- Infra: `nginx.conf` gains a static `/files/` location serving the
  uploads directory directly; `docker-compose.yml` mounts that same host
  uploads directory into the `frontend` service read-only so nginx can
  reach it.
- Frontend: `frontend/public/w/feed/upload/index.html` moves to
  `frontend/public/w/feed/files/index.html` with the new collapsible
  form, file list, and refresh/open/delete controls; `nginx.conf` route
  updated from `/w/[^/]+/feed/upload` to `/w/[^/]+/feed/files`; tab nav
  label/id updated on both the ask and content pages.
- Specs: `openspec/specs/document-upload/spec.md` (delta),
  `openspec/specs/document-management/spec.md` (new).
