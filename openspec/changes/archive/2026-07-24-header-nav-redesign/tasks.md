## 1. Theme toggle foundation

- [x] 1.1 In `frontend/public/style.css`, restructure the dark-mode token
      overrides: keep `@media (prefers-color-scheme: dark)` as the default,
      add `html[data-theme="dark"] .origami-world { ... }` with the same
      overrides, and add `html[data-theme="light"] .origami-world { ... }`
      forcing the light values (for users overriding a dark OS).
- [x] 1.2 Add a small inline script in `frontend/public/partials/head.html`
      (or equivalent, loaded before first paint) that reads the `theme` key
      from `localStorage` and sets `data-theme` on `<html>` accordingly, to
      avoid a flash of the wrong theme.
- [x] 1.3 Vendor two inline SVGs (sun, moon) from Lucide (ISC license) into
      `frontend/public/partials/nav.html`, with a header comment following
      the existing vendoring convention (name, license, source URL, date —
      match `alpine.min.js`'s comment format).
- [x] 1.4 Add a theme toggle button to `nav.html`, styled with the existing
      `.origami-button-secondary` class, showing the *destination* icon
      (moon + `aria-label="Switch to dark theme"` while in light mode, sun +
      `aria-label="Switch to light theme"` while in dark mode). Clicking it
      flips `data-theme` on `<html>` and writes the choice to `localStorage`.

## 2. Header/nav restructure

- [x] 2.1 Reorder `nav.html` markup into two flex groups: left (Home,
      Workspaces, Beta), right (theme toggle, then Login/Register or the
      logged-in state).
- [x] 2.2 Change the Beta badge from `<span class="beta-badge">` to
      `<a class="beta-badge" href="/beta">`, keeping the existing CSS class,
      and add a hover state reusing the `.origami-button-secondary` hover
      pattern (`var(--og-accent-fill)` background swap) so it reads as
      clickable.
- [x] 2.3 Convert the hand-rolled login/logout `<script>` in `nav.html` to
      an Alpine `x-data` component (reads `Auth.isLoggedIn()`/email on
      init, `x-show`/`x-text` for logged-in vs logged-out state, logout
      click calls `Auth.clearSession()` + navigates).
- [x] 2.4 Update the "Login / Register" nav link(s) to a single link
      pointing at `/login`.
- [x] 2.5 In `style.css`, add `flex-wrap: wrap` to `.origami-world nav` and
      give the right-hand group `margin-left: auto` (replacing the current
      `.beta-badge`-specific `margin-left: auto`), so the right group wraps
      to its own line on narrow viewports instead of squishing. No
      hamburger menu.

## 3. Combined login/register page

- [x] 3.1 Update `frontend/public/login/index.html` to contain two forms:
      the existing login form (heading "Log in") using `apiForm()` posting
      to `/api/auth/login`, and a register form (heading "Register",
      reusing the current `register/index.html` markup/fields — email +
      password only, no confirm-password field) using `apiForm()` posting
      to `/api/auth/register`. Layout: two columns on desktop, Login left /
      Register right; stacked on mobile with Login first, Register below.
      Update the page's overall `<h1>` to "Log in or register".
- [x] 3.2 Update in-page cross-link text (previously "Need an account?
      Register" / "Already have an account? Log in") to reflect that both
      forms now live on the same page — remove links that pointed at the
      now-removed `/register` route. (Both forms now live on the same page,
      so the cross-links themselves are gone, not just retargeted.)
- [x] 3.3 Delete `frontend/public/register/` entirely.
- [x] 3.4 Grep the frontend for any remaining hardcoded `/register` links
      (e.g. other pages' footers/nav) and update them to `/login`. No
      redirect is added for an already-authenticated visitor hitting
      `/login` — out of scope, leave existing behavior as-is. (Grep
      confirmed no remaining `/register` page links — only the unrelated
      `/api/auth/register` endpoint call and prose comments.)

## 4. Design system documentation

- [x] 4.1 Update `DESIGN.md`'s component catalogue: add a "Theme Toggle"
      entry (button style, destination-icon convention, localStorage
      persistence) and update the existing "Beta Mark" entry to note it's
      now an interactive link with a hover state.

## 5. Verification

- [x] 5.1 Verified live in Chrome against `docker compose up` on isolated
      ports (8001/8081/5433): header shows Home/Workspaces/Beta left,
      toggle + Login/Register right; clicked the toggle on `/home` — icon
      and `aria-label` swap correctly (confirmed "Switch to light theme" /
      "Switch to dark theme" via accessibility tree) and the page
      recolors instantly; theme choice persisted through a client-side
      navigation to `/login` **and** a full page reload (`localStorage`
      read back as `"light"`, `data-theme="light"` on `<html>`); Beta badge
      hover fills with the accent color and text flips to dark; registered
      a real test user end-to-end from the combined page (redirected to
      `/workspaces`, nav flipped to email + Logout via the Alpine
      conversion) and logged out again; `/register` returns a real 404 in
      the browser; zero console errors the whole session. **Not
      confirmed**: actual narrow-viewport wrapping — `resize_window`
      didn't change the tab's rendering viewport in this browser session
      (an environment/tooling limitation, not something in the diff), so
      the `flex-wrap`/grid-collapse behavior is only verified by code
      review against the existing `max-width: 768px` breakpoint pattern
      already used elsewhere in `style.css`, not by an actual mobile-width
      screenshot.
- [ ] 5.2 Verify OS dark/light preference still governs the theme when no
      toggle choice has been made yet. Not verified — the test session
      only exercised the explicit-choice path (localStorage already had a
      value after the first toggle click); simulating OS
      `prefers-color-scheme` wasn't attempted.
- [x] 5.3 `git status` confirms zero files under `backend/` were touched by
      this change, so the backend test suite is unaffected. (Not
      re-run — no frontend test suite exists in this repo to run.)
