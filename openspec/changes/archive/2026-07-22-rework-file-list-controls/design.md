## Context

The Content page's file list (`frontend/public/w/feed/files/index.html`) is a
plain HTML/JS table with 3 columns — Name, Status, and an unlabeled actions
column holding only "Delete". Today, Name is a hyperlink to `file.url` that
opens the file's PDF in a new tab; there is no way to rename a file after
upload. The backend (`backend/app/api/files.py`) only exposes `POST`
(create), `GET` (list), and `DELETE` for files — no update endpoint exists.

The `display_name` column already has a per-workspace uniqueness constraint
(`uq_files_workspace_id_display_name` in `backend/app/db/models.py`), and
`create_file` already contains the duplicate-name check this design reuses
for renames.

This is a frontend-and-backend pair of changes with no new external
dependencies or data model changes, but it does replace a documented
requirement in `openspec/specs/document-management/spec.md`, so it goes
through the OpenSpec proposal flow per `AGENTS.md`.

## Goals / Non-Goals

**Goals:**
- Move "open file" off the display name and onto a dedicated "Open" button
  in the actions column, before "Delete".
- Let editors rename a file's `display_name` inline from the list, with
  clear Save/Cancel affordances and inline error feedback.
- Keep the existing access model: Open stays available to everyone (as
  opening already is today); Edit is gated the same way Delete already is
  (`canEdit`).

**Non-Goals:**
- No editing of file *content* (files remain PDFs opened via the browser's
  native viewer).
- No bulk rename, no rename history/audit trail.
- No change to `status`, `original_filename`, upload flow, or delete flow
  beyond column reflow.
- No optimistic in-place DOM patching — this reuses the existing
  refetch-the-list-after-mutation pattern already used by delete and upload.

## Decisions

- **Rename endpoint shape**: `PATCH /w/{slug}/files/{file_id}` with a JSON
  body `{"display_name": "..."}`, guarded by the same
  `require_workspace_edit_access` dependency `delete_file` already uses.
  Chosen over `PUT` because only one field is ever updated, and over adding
  a `rename` sub-route because `PATCH` on the existing resource path is the
  idiomatic partial-update verb this API doesn't yet use anywhere else, but
  is the closest existing REST convention to fit.
- **Duplicate-name check excludes the current row**: `create_file`'s
  existing check (`backend/app/api/files.py:87-97`) queries for any file in
  the workspace with the target `display_name`. For rename, that query must
  add `File.id != file_id`, otherwise saving a name unchanged (the common
  "no-op edit") would find the file's own current row and reject with a
  false conflict.
- **Validation split between client and server**: the input can be
  trimmed client-side for a snappier experience, but the server is the
  source of truth for both "non-blank" and "unique in workspace" — the
  client only ever surfaces whatever the server decides (400 for blank,
  409 for conflict), rather than duplicating validation logic in JS that
  could drift from the backend's rules.
- **Inline edit lives entirely in `index.html`'s existing vanilla-JS
  pattern**: no new JS module, no framework. `renderFiles()` gains a
  per-row "edit mode" flag; entering edit mode swaps the name `<td>`'s
  children for an `<input>` + Save/Cancel buttons; leaving edit mode (via
  Cancel, or a successful Save) goes through the existing `loadFiles()`
  refetch, consistent with `deleteFile()`.
- **Open button reuses the exact link semantics**: `window.open(file.url,
  "_blank", "noopener")` mirrors the current `<a target="_blank"
  rel="noopener">` behavior exactly, so no change in how the PDF opens.
- **Error display**: a small text node inserted next to the input (not a
  toast, not `alert()`), matching the low-key inline-error style already
  used for the upload form's `#upload-result`.

## Risks / Trade-offs

- **Losing in-progress edits on Refresh**: if a user clicks the page's
  "Refresh" button while mid-edit on a row, `loadFiles()` will re-render
  the whole table and drop their in-progress edit. → Accepted: this matches
  today's behavior for any other row-level transient state, and is a rare
  interaction (refresh is meant for polling file `status`, not something
  users click while renaming).
- **Race between two editors renaming the same file, or renaming to a name
  another editor just took**: the backend's uniqueness check is the final
  guard; the client simply surfaces whatever 409 comes back. → Accepted, no
  additional locking needed given existing app doesn't have any concurrent-
  edit protection elsewhere either.
- **Removing the name-link is a breaking UI change** for anyone relying on
  clicking the name to open a file. → Mitigated by the new "Open" button
  being immediately visible in the same row, and by this being called out
  as **BREAKING** in the proposal.

## Migration Plan

- No data migration needed (reuses the existing `display_name` column and
  constraint).
- Deploy backend and frontend together: the new frontend calls the new
  `PATCH` route, so the backend change should ship in the same release (or
  first, since it's additive and doesn't remove any existing route).
- Rollback is a plain revert of both changes; no destructive schema change
  to undo.

## Open Questions

None outstanding — all UX and validation decisions were resolved with the
user before this proposal was drafted.
