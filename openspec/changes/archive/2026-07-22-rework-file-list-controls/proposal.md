## Why

The Content page's file list currently overloads the file name as the only
way to open a file (a link with a "↗" icon), and offers no way to rename a
file after upload. Users want the name to be an ordinary, renamable label —
edited inline via a small "Edit" control — with opening moved to its own
"Open" button alongside "Delete".

## What Changes

- **BREAKING**: The file name in the file list is no longer a clickable
  link. Clicking it does nothing; it is now a plain label.
- Add an "Edit" control next to each file's display name, visible only to
  users who can edit the workspace. Clicking it turns the name into a text
  input with **Save**/**Cancel** controls (Enter saves, Escape cancels).
- Add a new backend endpoint (`PATCH /w/{slug}/files/{file_id}`) to rename a
  file's `display_name`, enforcing the same non-blank and per-workspace
  uniqueness rules upload already enforces, excluding the file's own row.
- Renaming to a blank or already-used name shows an inline error next to the
  input and leaves the input open for retry; it does not use `alert()`.
- Add a new "Open" button to the actions column, positioned before
  "Delete", which opens the file's existing content URL in a new tab. Unlike
  Edit and Delete, Open remains visible regardless of edit access, matching
  today's behavior where anyone can open a file.
- Remove the now-unused link/icon styling for the old name-link.

## Capabilities

### New Capabilities

(none — this only changes existing file-list behavior)

### Modified Capabilities

- `document-management`: the requirement that "the display name SHALL
  itself be the control that opens the file" is replaced by a plain-text
  name with a separate Edit control and a separate Open button; a new
  requirement is added for renaming a file's display name (validation,
  errors, and access gating).

## Impact

- Frontend: `frontend/public/w/feed/files/index.html` (`renderFiles()`,
  plus a new `renameFile()` request function) and `frontend/public/style.css`
  (drop now-dead `.file-open-link`/`.open-icon` rules).
- Backend: `backend/app/api/files.py` (new `PATCH` route), `backend/app/schemas.py`
  (new rename request schema).
- Spec: `openspec/specs/document-management/spec.md` requirements for the
  content-page file list and its access-gated controls.
- No database schema changes — reuses the existing `display_name` column and
  its existing per-workspace uniqueness constraint.
