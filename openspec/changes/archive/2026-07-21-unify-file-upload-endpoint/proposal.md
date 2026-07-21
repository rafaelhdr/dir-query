## Why

`app/api/uploads.py` and `app/api/files.py` both operate on the same
`File` model/table — there is no separate `Upload` entity. The split is a
verb-based one (create vs. read/delete) rather than a real bounded-context
boundary: both modules independently import `UPLOAD_DIR`/`File`/`Workspace`
and independently recompute the same on-disk path
(`UPLOAD_DIR / workspace_id / filename`), `tests/test_files.py` already
imports and monkeypatches `app.api.uploads` just to create a file to
list/delete, and the frontend already treats create/list/delete as one
"Content" feature hitting two inconsistently named paths
(`POST .../uploads` vs. `GET`/`DELETE .../files`). Consolidating removes
the duplicated path logic and the artificial module/URL boundary.

## What Changes

- Move `create_upload` from `app/api/uploads.py` into `app/api/files.py` as
  `POST /w/{slug}/files`. **BREAKING**: `POST /w/<slug>/uploads` no longer
  resolves.
- Delete `app/api/uploads.py`; `app/main.py` no longer registers a separate
  uploads router.
- Update the frontend's upload `fetch` call
  (`frontend/public/w/feed/files/index.html`) to POST to `/api/w/{slug}/files`.
- Fold `tests/test_uploads.py` into `tests/test_files.py` (one test module
  per router, per `AGENTS.md` convention).

No validation, storage, or indexing behavior changes — only which module
the handler lives in and which URL it's served from.

## Capabilities

### Modified Capabilities
- `document-upload`: the one requirement that names the literal endpoint
  path ("Uploading to an owned workspace requires the owner's session")
  changes `POST /w/<slug>/uploads` to `POST /w/<slug>/files`. All other
  requirements, scenarios, and behavior are unchanged.

`document-management` is unaffected — it already only describes
`GET`/`DELETE /w/<slug>/files`, which don't move.

## Impact

- Backend: `app/api/files.py` (gains the create handler), `app/api/uploads.py`
  (deleted), `app/main.py` (drop the `uploads` router registration).
- Frontend: `frontend/public/w/feed/files/index.html` (upload fetch URL).
- Tests: `tests/test_uploads.py` (deleted, folded into `tests/test_files.py`).
- Specs: `openspec/specs/document-upload/spec.md` (delta — path reference only).
