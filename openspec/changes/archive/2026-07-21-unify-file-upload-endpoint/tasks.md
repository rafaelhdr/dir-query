## 1. Backend

- [x] 1.1 Merge `create_upload`'s logic (helper + handler) from `app/api/uploads.py` into `app/api/files.py` as `create_file`, routed at `POST /w/{slug}/files`
- [x] 1.2 Delete `app/api/uploads.py`
- [x] 1.3 Remove the `uploads` import and router registration from `app/main.py`

## 2. Frontend

- [x] 2.1 Update the upload `fetch` call in `frontend/public/w/feed/files/index.html` to `POST /api/w/{slug}/files`

## 3. Tests

- [x] 3.1 Fold `tests/test_uploads.py`'s tests into `tests/test_files.py`, updating request paths from `/w/{slug}/uploads` to `/w/{slug}/files`
- [x] 3.2 Simplify `tests/test_files.py`'s fixture to only monkeypatch `files_module` (drop the now-unneeded `uploads_module` patches)
- [x] 3.3 Delete `tests/test_uploads.py`

## 4. Verification

- [x] 4.1 Run the full backend pytest suite
- [x] 4.2 Confirm no remaining `/uploads` API path references (`grep -rn "/uploads" backend frontend openspec/specs`, excluding unrelated `UPLOAD_DIR`/storage-path naming)
- [x] 4.3 Manually verify in the running app: upload, list, delete a file on a workspace's Content page (verified via curl against the running `docker compose` backend: create/list/delete all succeed at the new `/files` path, and the old `POST /w/<slug>/uploads` now 404s; browser extension wasn't connected to drive the actual page, but the frontend change is a one-line fetch-URL string swap exercising the identical request)
