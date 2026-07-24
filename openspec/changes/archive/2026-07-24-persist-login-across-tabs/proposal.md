## Why

Login state currently lives in `sessionStorage`, which is scoped per browser
tab. A user who opens the app in a new tab is shown as logged out even
though they never logged out, forcing them to log in again in every new
tab. The expectation is that a login stays active across tabs until the
user explicitly logs out.

## What Changes

- Store the auth token in `localStorage` instead of `sessionStorage`, so a
  new tab or window of the same browser sees an existing login
  immediately. **BREAKING**: the `user-auth` spec's current requirement
  that a new tab starts logged out is reversed.
- The 18-hour token expiry is unchanged — this only fixes the new-tab
  case, not how long a token remains valid overall.
- When a user logs out in one tab, other open tabs detect it via the
  browser's `storage` event and immediately reflect the logged-out state,
  rather than only discovering it on their next request or reload.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `user-auth`: the token storage mechanism changes from `sessionStorage`
  to `localStorage`, reversing the "new tab starts logged out" requirement
  to "new tab starts logged in if any tab is." Adds a requirement that
  logout in one tab is propagated to other open tabs via the `storage`
  event.

## Impact

- `frontend/public/auth.js`: switch `sessionStorage` calls to
  `localStorage`, add a `storage` event listener that reacts to the token
  key being cleared.
- `frontend/public/partials/nav.html`: logout-triggered UI state should
  react the same way whether triggered locally or via the cross-tab
  listener.
- No backend changes. Token issuance, expiry, and validation
  (`backend/app/services/auth.py`, `backend/app/api/auth.py`) are
  unaffected.
