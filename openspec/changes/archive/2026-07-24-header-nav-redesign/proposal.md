## Why

The current header has four separate nav links (`Home | Workspaces | Login |
Register`) with the Beta badge floated to the far right as inert text, and
Login/Register are two separate pages with duplicated form styling. This
splits a single "authenticate" intent across two routes, gives Beta no
click target even though a Beta info page already exists, and gives users
no way to override the site's dark/light theme (currently OS-preference
only). This change consolidates the header into a clearer layout, merges
login/register into one page, makes Beta a real link, and adds a
user-controlled theme toggle.

## What Changes

- Reorder the header: **Left** = Home, Workspaces, Beta; **Right** = theme
  toggle button, then a single "Login / Register" link.
- Turn the Beta badge into a link to the existing `/beta` page (was inert
  text).
- **BREAKING**: Merge `/login` and `/register` into a single `/login` page
  (login form and register form side by side, stacked on mobile). Remove
  the standalone `/register` route/page entirely — no redirect.
- Add a dark/light theme toggle button in the header. The user's explicit
  choice is stored in `localStorage` and overrides the OS-level
  `prefers-color-scheme` default; with no stored choice, OS preference
  still governs.
- Convert `partials/nav.html`'s hand-rolled login/logout `<script>` to
  Alpine.js, closing the one remaining non-Alpine piece flagged in the
  htmx→Alpine migration.

## Capabilities

### New Capabilities

- `theme-toggle`: user-controlled dark/light theme override, persisted in
  `localStorage`, available from every page's header.

### Modified Capabilities

- `user-auth`: the "frontend attaches the stored token to API requests"
  requirement currently specifies separate pages at `/register` and
  `/login`. It's updated to specify a single combined page at `/login`
  serving both forms; `/register` no longer exists.
- `home-page`: the "Home page discloses beta status" requirement currently
  describes a badge with no requirement that it link anywhere. It's updated
  to require the badge link to `/beta`.

## Impact

- `frontend/public/partials/nav.html` — reorder links, beta badge becomes a
  link, add theme toggle button, convert login/logout script to Alpine.
- `frontend/public/login/index.html` — becomes the combined login+register
  page.
- `frontend/public/register/index.html` — deleted.
- `frontend/public/style.css` — theme toggle button style (reuse
  `.origami-button-secondary`), `[data-theme]` selectors alongside the
  existing `prefers-color-scheme` media query, combined-page layout CSS.
- No backend changes — `/api/auth/login` and `/api/auth/register` endpoints
  and `backend/app/api/auth.py` are unaffected; both forms already share
  `apiForm()` in `frontend/public/auth.js`.
