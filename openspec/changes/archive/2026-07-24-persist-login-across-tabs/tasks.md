## 1. Switch token storage to localStorage

- [x] 1.1 In `frontend/public/auth.js`, change `getToken`, `getEmail`, and
      `setSession` to read/write `localStorage` instead of
      `sessionStorage`.
- [x] 1.2 In `frontend/public/auth.js`, change `clearSession` to remove
      the keys from `localStorage` instead of `sessionStorage`.

## 2. Propagate logout to other tabs

- [x] 2.1 In `frontend/public/partials/nav.html`'s Alpine component, add a
      `window.addEventListener('storage', ...)` handler (e.g. in an
      `init()` hook) that checks whether the changed key is the auth
      token key and its new value is empty/null.
- [x] 2.2 When that condition is met, update the component's `loggedIn`
      and `email` state to reflect logged-out, the same way the local
      `logout()` method does.

## 3. Manual verification

- [x] 3.1 Log in in one tab, open a second tab of the same app, and
      confirm the second tab shows the logged-in state without logging in
      again.
- [x] 3.2 With both tabs open and logged in, click logout in one tab and
      confirm the other tab's nav updates to logged-out without a reload.
- [x] 3.3 Confirm a fresh tab opened before any login still shows a
      logged-out state (no false-positive login).
