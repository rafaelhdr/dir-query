## Context

`workspaces` currently has required `owner_email` and `password`
columns (`backend/app/db/models.py`). The password is hashed with
Postgres `pgcrypto` (`func.crypt(password, func.gen_salt("bf"))`,
`backend/app/api/workspaces.py:40`) but is never verified anywhere —
no endpoint checks it. `owner_email` is documented as
"internal/administrative contact only" and is never exposed in API
responses. There is no `users` table, no session/token mechanism, and
no auth library installed.

The frontend is server-rendered static HTML + htmx with no JS build
step (`AGENTS.md`), served by Nginx, which reverse-proxies `/api/` to
the backend on the same origin (`frontend/nginx.conf`) — so there is
no cross-origin concern between frontend and backend. Several pages
already use hand-written vanilla `fetch()` calls alongside htmx
attributes (e.g. `frontend/public/w/feed/files/index.html`), so adding
a small hand-written auth script is consistent with the existing code,
not a new pattern.

## Goals / Non-Goals

**Goals:**
- Let a visitor register (email + password) and log in, receiving a
  token the frontend can use to authenticate subsequent requests.
- Let workspace creation optionally attach an owner (the logged-in
  user), while remaining fully usable with no login at all.
- Restrict "edit" actions (upload, delete) on an owned workspace to its
  owner, while leaving ownerless workspaces open to everyone.
- Reuse the existing pgcrypto password-hashing approach for user
  passwords rather than introducing a second hashing scheme.

**Non-Goals:**
- Server-side session/token revocation (blacklisting) before natural
  expiry.
- Refresh tokens / silent renewal.
- Email verification, password reset, or account recovery flows.
- Cleaning up anonymous workspaces after 2 hours (future work).
- Letting a user later claim an existing anonymous workspace.
- Rate limiting or brute-force protection on login (not requested;
  can follow later if needed).

## Decisions

### Token mechanism: JWT bearer token, not a cookie session
The frontend attaches the token via a small script that listens for
htmx's `configRequest` event (and wraps `fetch`) to set
`Authorization: Bearer <token>` on outgoing requests, following the
pattern in [htmx's async-auth example](https://htmx.org/examples/async-auth/).
Alternative considered: an httponly cookie session, which would be
auto-sent by the browser with zero client script needed (this app is
same-origin). Rejected in favor of the bearer-token approach per
explicit product direction.

### Token storage: `sessionStorage`
The app is multi-page (separate static HTML per route via Nginx
`try_files`, not an SPA), so an in-memory-only variable (as shown in
the raw htmx example) would be wiped on every navigation, forcing
re-login constantly. `sessionStorage` survives full-page navigation
within a tab and clears when the tab closes, bounding how long a
stolen token (via any future XSS) stays usable, versus `localStorage`
which persists indefinitely.

### Token lifetime: 18 hours, no refresh token
A single token issued at login/register, valid for 18 hours, after
which the user must log in again. No refresh endpoint, no
refresh-token storage/rotation. Matches the "simple login system"
scope — this token only gates who may add/remove files in a workspace,
not access to sensitive data, so the exposure window is an acceptable
trade-off for avoiding a second token type and its storage/rotation
logic.

### Logout: client-side only
Logout clears the token from `sessionStorage`. No server-side
blacklist/revocation table. A captured token remains valid until its
18h expiry regardless of logout — consistent with the "no refresh
token" simplicity call, and acceptable given what the token gates.

### Password hashing: reuse the existing pgcrypto pattern
`users.password` is hashed identically to `workspaces.password` today:
`func.crypt(password, func.gen_salt("bf"))` on write, and
`func.crypt(input_password, users.password) = users.password` on
login. No new hashing library; the JWT signing key is unrelated to
this and is a separate concern (see below).

### JWT signing key: new required secret, existing `_read_secret()` pattern
`app/config.py` gains `JWT_SECRET_KEY`, read via the existing
`_read_secret()` helper (checks `JWT_SECRET_KEY_FILE` /
`/run/secrets/jwt_secret_key.txt`, falls back to the `JWT_SECRET_KEY`
env var), matching how `MINIMAX_API_KEY` / `GOOGLE_API_KEY` are
supplied. A new `secrets/jwt_secret_key.txt.example` is added. Signed
with HS256 (single backend service verifies its own tokens; no need
for asymmetric keys). Like `MINIMAX_API_KEY`/`GOOGLE_API_KEY`, a
missing key does not crash backend startup — it raises a clear
`RuntimeError` the first time token signing/verification is actually
attempted, matching the existing lazy-credential-check convention in
`index_service.py`.

### Workspace ownership: nullable FK, not a second owner-password
`workspaces.owner_email` and `workspaces.password` are dropped;
`workspaces.owner_user_id` (nullable FK to `users.id`,
`ON DELETE SET NULL`) replaces them. `NULL` means the workspace is
ownerless/public — created without authentication. This is a
destructive migration (existing rows lose `owner_email`/`password`
data), judged acceptable since the password was never functionally
used and this is pre-launch.

### Ownership resolution at creation: implicit from the request's own token
`POST /workspaces` no longer takes owner fields. If the request
carries a valid `Authorization` bearer token, `owner_user_id` is set
to that token's user id; otherwise it's left `NULL`. No explicit
"make this public" flag — it's simply the absence of a valid session.

### Authorization checks: owner-only when an owner exists, open otherwise
`POST /w/{slug}/uploads` and `DELETE /w/{slug}/files/{id}` load the
workspace, and:
- if `owner_user_id` is `NULL`: allow the request unconditionally
  (anonymous or not).
- if `owner_user_id` is set: require a valid token whose user id
  matches; otherwise reject (401 if no/invalid token, 403 if a valid
  token for a different user).

`POST /w/{slug}/ask` and the conversation-history endpoints are
unchanged — no auth check, open to everyone, as today.

### Exposing "can I edit this" without exposing who owns it
`GET /workspaces` and `GET /workspaces/{slug}` compute `can_edit` from
the requester's own (optional) token compared against
`owner_user_id`, and return only that boolean — never `owner_user_id`
or any owner identity, preserving the existing "owner identity is
never public" stance from the current spec.

### Frontend: hide, don't disable, restricted controls
The content page (`/w/<slug>/feed/files`) fetches the workspace (now
including `can_edit`) and renders the "Add content" section and each
file's "Delete" button only when `can_edit` is `true`. Non-owners
viewing an owned workspace see a read-only page; anyone viewing an
ownerless workspace sees full edit controls. The backend enforces this
regardless of what the frontend renders.

## Risks / Trade-offs

- **Stolen token stays valid up to 18h after logout** (no revocation)
  → Accepted: the token only gates workspace edit rights, not
  sensitive personal data; keeps the implementation simple as directed.
- **`sessionStorage` token is JS-readable, so any future XSS could
  exfiltrate it** → Mitigated by scope (cleared per-tab, 18h max
  lifetime) rather than eliminated; a stricter posture (httponly
  cookie) was considered and explicitly not chosen.
- **Destructive migration drops `owner_email`/`password` data** →
  Acceptable pre-launch; no functional behavior depended on the
  password today, and `owner_email` was contact-only.
- **No password strength requirement (beyond non-empty)** → Matches
  existing workspace-password behavior; accepted as consistent with
  the "simple" brief.
- **No login rate-limiting** → Not requested; flagged here as a
  reasonable follow-up rather than blocking this change.

## Migration Plan

1. Alembic migration: create `users` table; add nullable
   `workspaces.owner_user_id` FK; drop `workspaces.owner_email` and
   `workspaces.password`.
2. Add `JWT_SECRET_KEY` secret plumbing (`config.py`, `docker-compose.yml`
   env passthrough, `secrets/jwt_secret_key.txt.example`) before the
   backend depends on it at import/startup time.
3. Ship backend changes (auth router, ownership checks, `can_edit`)
   and frontend changes (register/login pages, updated workspace-new
   form, owner-aware content page, token-attaching script) together —
   the frontend depends on `can_edit` existing in the API response.
4. No rollback data migration is provided for
   `owner_email`/`password` (irreversibly dropped); rolling back this
   change means restoring from a pre-migration backup if that data is
   ever needed.

## Open Questions

None outstanding — scope and behavior were confirmed directly with the
product owner before writing this design.
