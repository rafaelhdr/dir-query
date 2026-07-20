## 1. Database

- [x] 1.1 Add a partial/plain unique index on `files (workspace_id, original_name)` in `app/db/models.py`
- [x] 1.2 Write an Alembic migration adding that unique constraint

## 2. Backend: upload with editable name + duplicate validation

- [x] 2.1 In `app/api/uploads.py`, accept a `name` form field alongside `file`, defaulting to the picked file's filename when not provided
- [x] 2.2 Use `name` as `original_name` when creating the `File` row
- [x] 2.3 Catch the unique-constraint `IntegrityError` on insert and return `409 Conflict` with a clear message, without persisting the file to disk (or cleaning it up if already written)

## 3. Backend: list, delete endpoints

- [x] 3.1 Create `app/api/files.py` with a router scoped to `/w/{slug}/files`, using `get_workspace_by_slug`
- [x] 3.2 Add `GET /w/{slug}/files` returning `{"data": [...]}` with each file's `id`, `original_name`, `status`, `uploaded_at`, and `url` (built from `workspace_id` + stored `filename`, e.g. `/files/{workspace_id}/{filename}`)
- [x] 3.3 Add `DELETE /w/{slug}/files/{file_id}`: 404 if not found/wrong workspace, else delete the DB row (commit), then unlink the file from disk
- [x] 3.4 Register the new router in `app/main.py`

## 4. Infra: serve uploaded files directly via nginx

- [x] 4.1 Add a static `location /files/ { alias ...; }` block to `nginx.conf` serving the uploads directory, matching the `{workspace_id}/{filename}` layout the `url` field uses
- [x] 4.2 Mount the host uploads directory (`./backend/data/uploads`) into the `frontend` service in `docker-compose.yml`, read-only, at the path the `alias` targets
- [x] 4.3 Verify nginx serves `.pdf` files with a content type that renders inline in the browser (default `mime.types`), not as a forced download

## 5. Frontend: move and rename the page

- [x] 5.1 Move `frontend/public/w/feed/upload/index.html` to `frontend/public/w/feed/files/index.html`
- [x] 5.2 Update `nginx.conf`: replace the `/w/[^/]+/feed/upload` location with `/w/[^/]+/feed/files`
- [x] 5.3 Update the tab bar on both the ask page and the content page: id `tab-upload` → `tab-files` (matching the new URL segment), text "Upload" → "Content", link target `/w/<slug>/feed/files`

## 6. Frontend: collapsible add-content form

- [x] 6.1 Wrap the upload form in a `<details>`/`<summary>` "Add content" section, collapsed by default
- [x] 6.2 Add an editable display-name text input; on file selection, prefill it with the picked file's filename
- [x] 6.3 Submit both `file` and `name` in the upload request
- [x] 6.4 On success, clear the file input and name field, collapse or leave the section per existing UX, and trigger a list refresh
- [x] 6.5 On a 409 duplicate-name conflict, show a clear inline error without clearing the user's entered fields

## 7. Frontend: file list + refresh/open/delete

- [x] 7.1 Add a refresh button above the file list and a list container below the add-content section
- [x] 7.2 Implement a `loadFiles()` function that fetches `GET /api/w/{slug}/files`, reads `data`, and renders each row with name, status, an "Open" link (`target="_blank"`, `href` set directly to that entry's `url`), and a "Delete" button
- [x] 7.3 Call `loadFiles()` on initial page load, on refresh-button click, and after a successful upload
- [x] 7.4 Wire the "Delete" button to `DELETE /api/w/{slug}/files/{file_id}`, then re-run `loadFiles()` on success

## 8. Verification

- [x] 8.1 Add/update backend tests: duplicate-name upload rejection, list envelope shape (including `url`), delete cascades to chunks and removes the disk file, delete/list 404 on wrong workspace
- [x] 8.2 Manually verify in the running app: upload with autofilled/edited name, duplicate-name rejection, list shows pending → indexed after refresh, open button opens the PDF in a new tab (served by nginx), delete removes the file and its chunks, and its `url` then 404s

## 9. Follow-up: split display name and original filename

- [x] 9.1 In `app/db/models.py`, add `original_filename` (not null), rename `original_name` → `display_name`, replace the single combined unique index with two: `(workspace_id, display_name)` and `(workspace_id, original_filename)`
- [x] 9.2 Write a migration: add `original_filename` nullable, backfill it from the existing `original_name` column, set it `NOT NULL`, rename `original_name` → `display_name`, drop the old combined unique index, create the two new per-field unique indexes
- [x] 9.3 In `app/api/uploads.py`, set `display_name` from the `name` form field (unchanged fallback to the picked file's filename) and `original_filename` from the picked file's filename (always, not user-editable)
- [x] 9.4 Pre-check both fields for an existing conflict before inserting, returning a `409` naming which field conflicted (display name vs. original filename); keep the `IntegrityError` catch as a race-condition fallback with a generic message
- [x] 9.5 In `app/api/files.py`, update the list response to include both `display_name` and `original_filename` (replacing the single `original_name` key)

## 10. Follow-up: name-as-open-link + original filename column

- [x] 10.1 In `frontend/public/w/feed/files/index.html`, remove the separate "Open" column; render the file's display name as an `<a target="_blank">` link (with `rel="noopener"`) pointing at its `url`, with a small icon indicating it opens in a new tab
- [x] 10.2 Add an "Original filename" column showing each file's `original_filename`
- [x] 10.3 Add minimal CSS for the name-link + icon in `frontend/public/style.css`
- [x] 10.4 Update/add backend tests for the two-field split (duplicate display name rejected, duplicate original filename rejected independently, same original filename allowed across workspaces, list response includes both fields)
- [x] 10.5 Manually verify: uploading a file whose original filename collides (but display name doesn't) is rejected, and vice versa; the file list shows both names; clicking the display name opens the file in a new tab

## 11. Follow-up: remove the original filename column from the UI

- [x] 11.1 In `frontend/public/w/feed/files/index.html`, remove the "Original filename" `<th>` and its per-row `<td>`; `original_filename` remains tracked and validated server-side, just not shown in the list UI
