## Why

Workspace creation currently forces every workspace to have an owner
email and password, but that password is never actually checked
anywhere — there is no login, and no endpoint restricts who can add or
remove content. This change introduces real user accounts (email +
password) and makes ownership optional at workspace-creation time:
workspaces created by a logged-in user are editable only by that user,
while workspaces created without logging in stay fully public and
editable by anyone, matching how the product is meant to work for
casual/anonymous use.

## What Changes

- Add user registration (email + password) and login, issuing a
  short-lived JWT (18h) that the frontend attaches to API requests via
  an `Authorization` header (stored in `sessionStorage`, attached
  through an htmx `configRequest`-style listener). Logout is
  client-side only (clears the stored token); no server-side token
  revocation.
- User passwords are hashed the same way workspace passwords are
  today: Postgres `pgcrypto`'s `crypt(password, gen_salt('bf'))`.
- **BREAKING**: Workspace creation no longer accepts or requires
  `owner_email` / `password` fields. `workspaces.owner_email` and
  `workspaces.password` are dropped and replaced with a nullable
  `owner_user_id` foreign key to the new `users` table.
- Creating a workspace while authenticated sets `owner_user_id` to the
  requesting user; creating one without authentication leaves it
  `NULL` (anonymous/public workspace).
- Uploading a file and deleting a file are now restricted to the
  workspace's owner when the workspace has one (`owner_user_id` is set
  non-null); workspaces with no owner remain open to anyone, including
  anonymous requests. Asking questions and viewing conversation
  history remain open to everyone regardless of ownership.
- `GET /workspaces` and `GET /workspaces/{slug}` gain a computed
  `can_edit` boolean, derived from the requester's own token (if any)
  against that workspace's `owner_user_id`. Owner identity itself is
  never exposed in API responses, consistent with the existing
  `owner_email` privacy stance.
- Frontend: new `/register` and `/login` pages; the workspace creation
  form drops its email/password fields; the content page hides its
  upload form and each file's "Delete" button when `can_edit` is
  `false`.

Explicitly out of scope for this change: the 2-hour cleanup of
anonymous workspaces, and letting a logged-in user later "claim" an
existing anonymous workspace.

## Capabilities

### New Capabilities
- `user-auth`: email/password registration and login, JWT issuance and
  verification, and how the frontend attaches/stores the token.

### Modified Capabilities
- `workspace-management`: workspace creation no longer requires (or
  accepts) an owner email/password; ownership is now an optional link
  to a `users` row, set automatically from the requester's session at
  creation time; workspace responses gain a computed `can_edit` field.
- `document-upload`: uploading a file to an owned workspace now
  requires the request to be authenticated as that workspace's owner;
  uploads to an ownerless workspace remain unrestricted.
- `document-management`: deleting a file from an owned workspace now
  requires the request to be authenticated as that workspace's owner;
  deletes on an ownerless workspace remain unrestricted. Listing and
  opening files are unaffected.

## Impact

- **Backend**: new `app/db/models.py::User` model and Alembic
  migration (add `users`, alter `workspaces` to drop
  `owner_email`/`password` and add nullable `owner_user_id`); new
  `app/api/auth.py` router (`/auth/register`, `/auth/login`); a JWT
  helper (encode/decode, dependency for "current user, if any" and
  "current user, required"); `app/config.py` gains a required
  `JWT_SECRET_KEY` (via the existing `_read_secret()` pattern);
  `app/api/workspaces.py`, `app/api/uploads.py`, `app/api/files.py`
  updated for ownership checks; new `pyjwt` dependency.
- **Frontend**: new `frontend/public/register/` and
  `frontend/public/login/` pages; `frontend/public/workspaces/new/`
  loses its email/password fields; `frontend/public/w/feed/files/`
  gains owner-aware show/hide logic for its upload form and delete
  buttons; nav partial gains login-state-aware links; a small shared
  script for attaching the stored token to `fetch`/htmx requests.
- **Specs**: modifies `openspec/specs/workspace-management/spec.md`,
  `openspec/specs/document-upload/spec.md`,
  `openspec/specs/document-management/spec.md`; adds
  `openspec/specs/user-auth/spec.md`.
