## Context

`frontend/public/auth.js` currently stores the bearer token and email in
`sessionStorage`. Per-tab scoping means a brand new tab (or window) never
sees a token written by another tab, even within the same browser profile,
so the user appears logged out there. `frontend/public/partials/nav.html`
reads `Auth.isLoggedIn()` once on Alpine component init and only updates
its local `loggedIn`/`email` state when `logout()` runs in that same tab.

This is a frontend-only, plain JS codebase (no build step, no framework
beyond vendored Alpine.js) per `AGENTS.md`. The backend's token issuance,
18-hour expiry, and lack of server-side revocation (see `user-auth` spec)
are unaffected — this change is scoped to where the token lives in the
browser and how tabs learn about it.

## Goals / Non-Goals

**Goals:**
- A token written in one tab is immediately usable by any other tab/window
  of the same browser (same origin), including tabs opened before the
  login happened.
- A logout in one tab is reflected in other open tabs without requiring a
  reload or a failed request first.

**Non-Goals:**
- Changing token expiry, adding refresh/sliding-expiration, or any
  server-side session/revocation mechanism — the 18-hour hard expiry is
  unchanged (confirmed out of scope during requirements review).
- Switching to httpOnly cookies — rejected as a larger change (backend
  cookie handling, CORS/CSRF) than the problem calls for.
- Syncing state across different browsers/devices — this is same-browser,
  same-origin only, which is inherent to `localStorage`.

## Decisions

**Use `localStorage` instead of `sessionStorage` for the token/email.**
`localStorage` is shared across all tabs and windows of the same origin in
the same browser, which directly fixes the reported bug, and requires no
backend change. Alternative considered: httpOnly cookies set by the
backend — more secure against XSS token theft, but requires the backend to
set/read cookies on every authenticated route, handle CORS/CSRF, and
rework `Auth.fetch`'s bearer-header approach. Rejected as disproportionate
to the request, which is about tab scoping, not the security model of the
token itself.

**Use the native `storage` event for cross-tab logout sync.** The browser
fires a `storage` event in *other* tabs (not the one that made the change)
whenever `localStorage` is modified, including removal. Listening for the
token key being removed lets other tabs react immediately — no polling, no
new backend endpoint, no `BroadcastChannel` dependency. `nav.html`'s Alpine
component adds a listener that sets `loggedIn = false` and clears `email`
when it fires, matching what `logout()` already does locally.

**Keep `Auth.fetch`'s bearer-header attachment logic unchanged.** It
already reads the token via `getToken()` on every call; swapping the
underlying storage from `sessionStorage` to `localStorage` inside
`getToken`/`setSession`/`clearSession` is sufficient — no caller needs to
change.

## Risks / Trade-offs

- [`localStorage` has no expiry of its own, so a token persists in storage
  past the point a user might expect] → Mitigated by the backend's
  existing 18-hour JWT expiry: even though the token stays in storage,
  requests using an expired token are already rejected server-side.
- [`localStorage` is readable by any JS on the page, same as
  `sessionStorage` today, so this change doesn't newly introduce an XSS
  token-theft risk, but doesn't reduce the existing one either] → Accepted
  as out of scope; flagged here for visibility, not addressed by this
  change.
- [A user who logs in in one tab, then logs out in another, then switches
  back to the first tab expects it to reflect logged-out state] →
  Addressed by the `storage` event listener added to `nav.html`.

## Migration Plan

No data migration needed — this only changes where the frontend stores an
already-ephemeral token. On deploy, any user with an existing token in
`sessionStorage` simply logs in again once; there's no code path that
reads old `sessionStorage` values after this ships, which is acceptable
since tokens expire within 18 hours regardless.

Rollback is a plain revert of the two frontend files.
