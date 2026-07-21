## 1. Backend foundations

- [x] 1.1 Add `pyjwt` to `backend/pyproject.toml` and run `uv sync`
- [x] 1.2 Add `JWT_SECRET_KEY` to `backend/app/config.py` via the existing `_read_secret()` helper; raise a clear `RuntimeError` lazily on first use if unset (matching the `MINIMAX_API_KEY`/`GOOGLE_API_KEY` convention), not at startup
- [x] 1.3 Add `secrets/jwt_secret_key.txt.example` and document it alongside the existing MiniMax/Google secrets setup in `AGENTS.md`
- [x] 1.4 Add `JWT_SECRET_KEY_FILE`/`JWT_SECRET_KEY` plumbing to `docker-compose.yml` backend service env

## 2. Data model and migration

- [x] 2.1 Add `User` model to `backend/app/db/models.py` (`id`, `email` unique, `password`, `created_at`)
- [x] 2.2 Add nullable `owner_user_id` FK (`ON DELETE SET NULL`) to `Workspace` in `backend/app/db/models.py`, remove `owner_email` and `password` columns
- [x] 2.3 Generate Alembic migration: create `users` table, add `workspaces.owner_user_id`, drop `workspaces.owner_email` and `workspaces.password`
- [x] 2.4 Apply the migration locally and confirm `alembic upgrade head` runs clean on both dev and `_test` databases

## 3. Auth backend

- [x] 3.1 Create `backend/app/services/auth.py` (or similar) with password hash/verify helpers using `func.crypt(password, func.gen_salt("bf"))`, mirroring the existing workspace-password logic
- [x] 3.2 Add JWT encode/decode helpers (HS256, 18h expiry, `sub` = user id)
- [x] 3.3 Add FastAPI dependencies: `get_current_user_optional` (returns `User | None`, never raises) and `get_current_user_required` (raises 401 if missing/invalid/expired token)
- [x] 3.4 Create `backend/app/api/auth.py` with `POST /auth/register` (create user, lowercase email, reject duplicates, auto-issue token) and `POST /auth/login` (verify credentials, generic error on failure, issue token)
- [x] 3.5 Register the `auth` router in `backend/app/main.py`
- [x] 3.6 Add `backend/tests/test_auth.py` covering: register success, duplicate email rejected, register auto-login token works, login success, login wrong password rejected (generic error), login unknown email rejected (same generic error), case-insensitive email matching, expired/tampered token rejected on a protected endpoint

## 4. Workspace ownership

- [x] 4.1 Update `POST /workspaces` in `backend/app/api/workspaces.py`: drop `owner_email`/`password` form fields, set `owner_user_id` from `get_current_user_optional` if present, else leave `NULL`
- [x] 4.2 Add a `can_edit` computation helper (workspace has no owner, or current optional user id matches `owner_user_id`) and include it in `_workspace_public()` for both list and detail responses
- [x] 4.3 Update `backend/tests/test_workspaces.py`: creation without any credentials succeeds and is ownerless; creation while authenticated sets ownership; `can_edit` true/false/true-for-ownerless cases across list and detail endpoints; confirm no owner-identifying field ever appears in responses

## 5. Upload and delete ownership checks

- [x] 5.1 Add an ownership-check dependency/helper (e.g. in `backend/app/api/deps.py`) that, given a `Workspace` and the optional current user, raises 401 (no/invalid token) or 403 (valid token, wrong user) when the workspace has an owner and the requester isn't them, and no-ops when the workspace is ownerless
- [x] 5.2 Apply the ownership check to `POST /w/{slug}/uploads` in `backend/app/api/uploads.py`
- [x] 5.3 Apply the ownership check to `DELETE /w/{slug}/files/{file_id}` in `backend/app/api/files.py`
- [x] 5.4 Update `backend/tests/test_uploads.py`: owner can upload to their workspace, non-owner/anonymous rejected on an owned workspace, anyone can upload to an ownerless workspace
- [x] 5.5 Update `backend/tests/test_files.py`: same three cases for delete; confirm `GET /w/{slug}/files` (listing) and file-open URLs remain unrestricted regardless of ownership

## 6. Frontend: register and login

- [x] 6.1 Create `frontend/public/register/index.html`: email + password form, `fetch("/api/auth/register")`, store returned token in `sessionStorage`, redirect to `/workspaces` on success, show inline error on failure (e.g. duplicate email)
- [x] 6.2 Create `frontend/public/login/index.html`: same shape, posting to `/api/auth/login`, generic error message on failure
- [x] 6.3 Add a shared script (e.g. `frontend/public/partials/auth.js` or inline in `head.html`) that: reads the token from `sessionStorage`, attaches `Authorization: Bearer <token>` to htmx requests via an `htmx:configRequest` listener, and exposes a small helper for the page-level `fetch()` calls already used elsewhere in the codebase to attach the same header
- [x] 6.4 Update `frontend/public/partials/nav.html` to show "Register"/"Login" links when logged out and the user's email plus a "Logout" control (clears `sessionStorage`) when logged in, toggled client-side based on stored-token presence

## 7. Frontend: workspace creation and content page

- [x] 7.1 Update `frontend/public/workspaces/new/index.html`: remove the owner-email and password fields, keep only the name field, submit through the shared auth-attaching request helper so an existing session sets ownership
- [x] 7.2 Update `frontend/public/w/feed/files/index.html`: read `can_edit` from the workspace fetch response; hide the "Add content" section and every file's "Delete" button when `can_edit` is `false`; keep the file list, statuses, and open-in-new-tab links visible regardless

## 8. Spec sync and verification

- [x] 8.1 Run `uv run pytest -v` in `backend/` and confirm the full suite passes
- [x] 8.2 Manually verify end-to-end against the running docker-compose stack (browser extension unavailable in this environment, so verified via HTTP through the nginx proxy instead of visually): register two users, create an owned workspace, confirm `can_edit` is true for the owner and false for a non-owner/anonymous visitor; confirm upload/delete are 201/204 for the owner, 403 for a non-owner, 401 for anonymous; create a workspace while logged out and confirm anyone (unauthenticated) can upload/delete on it; confirm `POST /w/{slug}/ask` returns 200 (not 401/403) with no auth on an owned workspace; confirmed `/register`, `/login`, `/auth.js` are served and `/workspaces/new` no longer has owner/password fields — **visual UI/browser check still outstanding**
- [x] 8.3 Run `openspec validate add-user-auth --strict` and fix any reported issues
