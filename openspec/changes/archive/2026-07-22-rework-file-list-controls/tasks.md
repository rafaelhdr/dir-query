## 1. Backend: rename endpoint

- [x] 1.1 Add a `FileRename` request schema to `backend/app/schemas.py`
      (`display_name: str`), following the file's existing flat-`BaseModel`
      convention.
- [x] 1.2 Add `PATCH /w/{slug}/files/{file_id}` to `backend/app/api/files.py`,
      guarded by `require_workspace_edit_access` (same as `delete_file`),
      reusing `_get_workspace_file` to load the file.
- [x] 1.3 In the handler, trim the incoming `display_name` and reject blank
      values with `400`.
- [x] 1.4 Reuse the duplicate-name check pattern from `create_file`
      (`backend/app/api/files.py:87-97`) to reject a name already used by
      another file in the workspace with `409`, adding `File.id != file_id`
      so renaming to the file's own current name succeeds.
- [x] 1.5 On success, persist the new `display_name`, commit, refresh, and
      return the updated file via the existing `_file_public` helper.
- [x] 1.6 Add/extend a backend test module covering: successful rename,
      blank name (400), duplicate name (409), unchanged name (success),
      rename on a nonexistent file (404), and rename without edit access
      (403/401 per `require_workspace_edit_access`'s existing behavior).

## 2. Frontend: actions column — Open button

- [x] 2.1 In `renderFiles()` (`frontend/public/w/feed/files/index.html`),
      remove the `nameLink`/`openIcon` construction and its `file-open-link`
      class usage from the name cell — the name cell now renders
      `file.display_name` as plain text.
- [x] 2.2 Add a new "Open" `<button>` to the actions cell, inserted before
      the "Delete" button, that calls
      `window.open(file.url, "_blank", "noopener")` on click.
- [x] 2.3 Ensure the "Open" button renders unconditionally (not gated by
      `canEdit`), matching today's universal ability to open files.

## 3. Frontend: inline rename

- [x] 3.1 Add an "Edit" control next to the plain-text display name in the
      name cell, rendered only when `canEdit` is true (mirroring the
      existing `canEdit` gate around the "Delete" button).
- [x] 3.2 Wire "Edit" to swap that row's name cell into: a text `<input>`
      pre-filled with `file.display_name`, plus "Save" and "Cancel"
      buttons.
- [x] 3.3 Bind Enter (inside the input) to trigger the same action as
      "Save", and Escape to trigger the same action as "Cancel".
- [x] 3.4 Implement "Cancel" to discard the edit and re-render that row (or
      the whole list) back to its non-editing display, sending no request.
- [x] 3.5 Implement a `renameFile(fileId, newName)` function, following the
      request/refresh shape of the existing `deleteFile()`, that calls
      `Auth.fetch(".../files/" + fileId, { method: "PATCH", ... })` with the
      trimmed name as a JSON body.
- [x] 3.6 On a successful save response, call `loadFiles()` to refresh the
      list (matching the delete/upload refresh pattern) rather than
      patching the DOM in place.
- [x] 3.7 On a failed save response, keep the input and Save/Cancel
      controls visible, and render the backend's error detail as inline
      text next to the input (no `alert()`, no dialog).

## 4. Cleanup

- [x] 4.1 Remove the now-unused `.file-open-link` and `.open-icon` rules
      from `frontend/public/style.css` (currently lines 175-190).

## 5. Verification

- [x] 5.1 `cd backend && uv run pytest -v` — new/updated rename tests pass
      alongside the existing suite.
- [x] 5.2 `docker compose up --build`, then on a workspace's Content page
      as an editor: rename a file successfully (persists after reload),
      attempt a duplicate-name rename (inline error, input stays open),
      attempt a blank-name rename (inline error), cancel an in-progress
      edit (reverts, no request sent), click "Open" (file opens in a new
      tab), and confirm "Delete" still works.
- [x] 5.3 Reload the same page as a non-editor (`can_edit: false`) and
      confirm "Edit" and "Delete" are both absent while "Open" is still
      present and functional.
