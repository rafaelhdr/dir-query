## Context

The header (`frontend/public/partials/nav.html`) is included on every page
via Nginx SSI and currently renders: `Home | Workspaces | [Login/Register or
email+Logout]` on the left (via a hand-rolled login/logout `<script>`, the
one piece the htmx→Alpine migration left unconverted — see
`openspec/changes/archive/2026-07-23-migrate-htmx-to-alpine/design.md`), and
an inert `.beta-badge` `<span>` floated right via `margin-left: auto`
(`style.css`). `/login` and `/register` are separate static pages that
already share the `apiForm()` Alpine factory in `auth.js`, each posting to
its own backend endpoint (`/api/auth/login`, `/api/auth/register`) and
storing the returned token via `window.Auth` (`sessionStorage`-based).
There is no build step — everything is plain HTML/CSS/Alpine served
statically by Nginx (see `AGENTS.md`, Frontend development).

Theming today is entirely `prefers-color-scheme`-driven: `style.css`
defines `--og-*` custom properties on `.origami-world` for light, then
overrides them inside `@media (prefers-color-scheme: dark)`. No
localStorage/cookie override, no `Alpine.store`, no toggle UI exists
anywhere (confirmed by grep across the frontend).

## Goals / Non-Goals

**Goals:**
- Reorder the header to Left: Home, Workspaces, Beta (linked) / Right:
  theme toggle, "Login / Register" (or the existing logged-in state).
- Merge `/login` + `/register` into one page at `/login`, reusing the
  existing `apiForm()` pattern with no backend changes.
- Add a theme toggle that overrides `prefers-color-scheme` and persists via
  `localStorage`, defaulting to OS preference when unset.
- Convert nav's login/logout script to Alpine, matching the rest of the
  frontend.

**Non-Goals:**
- No backend/DB changes. Theme preference is device-local only, not tied to
  the `users` table.
- No redirect from `/register` to `/login` — the route is removed outright
  (explicit product decision), old bookmarks/links 404.
- No change to the `/api/auth/*` endpoints, `TokenResponse` shape, or
  `Auth`/`apiForm()` JS helpers beyond what's needed to point both forms at
  the same page.
- No new design tokens or button styles — theme toggle reuses
  `.origami-button-secondary`.

## Decisions

**1. Theme override mechanism: `data-theme` attribute on `<html>`, read by
CSS attribute selectors, written directly via `localStorage` (no
`Alpine.store` — see Decision 2).**

`style.css`'s dark values move from being reachable only via
`@media (prefers-color-scheme: dark)` to also being reachable via
`html[data-theme="dark"] .origami-world { ... }`, and the light values gain
an explicit `html[data-theme="light"] .origami-world { ... }` block. The
media query stays as the *default* (applies when no `data-theme` attribute
is present); the attribute selectors *override* it when the user has made
an explicit choice. This is a plain CSS cascade, not a JS-computed style, so
no flash-of-wrong-theme handling beyond a tiny inline script in `head.html`
that sets `data-theme` from `localStorage` before first paint (same reason
`auth.js` is loaded eagerly — avoid a visible flash).

Alternative considered: a `.theme-dark`/`.theme-light` class on `<body>`
instead of an attribute. Rejected only for taste — attribute selectors read
slightly cleaner for a tri-state (`unset` / `light` / `dark`) than class
presence/absence, no functional difference.

**2. Persistence: plain `localStorage`, no `Alpine.store`.**

A single key (e.g. `theme`) holding `"light" | "dark"` (absent = OS
default). Read/write directly via `localStorage.getItem`/`setItem` in the
nav's Alpine component — introducing `Alpine.store` for a single scalar
value used in one place would be more machinery than the problem needs.
`sessionStorage` (used by `Auth`) is intentionally *not* reused here: the
theme choice should survive across tabs/sessions, unlike the auth token.

**3. Combined `/login` page: two independent `apiForm()` instances on one
page, not a single shared form with a mode switch.**

Login and register already have different fields in spirit (register may
grow fields later, e.g. a display name) and different backend endpoints.
Keeping them as two separate `<div x-data="apiForm()">` blocks side by side
(CSS grid, two columns, `grid-template-columns: 1fr` i.e. stacked below a
breakpoint) posting to `/api/auth/login` and `/api/auth/register`
respectively avoids inventing a shared-state toggle component for no
reuse benefit — this mirrors the existing pattern exactly, just two copies
on one page instead of two pages.

**4. `/register` is deleted outright, no redirect.**

Confirmed product decision. Any hardcoded links to `/register`
(`login/index.html`'s existing cross-link, and any other page that happens
to reference it) are updated to `/login`. Nginx needs no config change: the
current config has no special-casing for `/login`/`/register` (matched by
the generic `location /` block), so removing the directory is sufficient —
Nginx will naturally 404 old `/register` requests.

**5. Nav login/logout script → Alpine, scoped to this change since it
touches the same file anyway.**

Replace the imperative `document.getElementById("nav-auth")` +
manual DOM building with an `x-data` component that reads
`Auth.isLoggedIn()`/`Auth.getEmail()` on init and re-renders declaratively
(`x-show`/`x-text`), calling `Auth.clearSession()` + a client-side
navigation on logout click — same behavior, idiomatic Alpine, matches every
other interactive piece of the frontend post-migration.

**6. Theme toggle icon: inline SVG sun/moon from Lucide, vendored directly
in `nav.html`, showing the destination state.**

No icon library or CDN — same reasoning as vendoring `alpine.min.js`
locally. Two small SVGs (sun, moon) are copied inline into `nav.html` with
a header comment following the existing vendoring convention (name,
license, source URL, date — see `alpine.min.js`'s comment for the exact
format). Lucide is ISC-licensed (no attribution required) and its minimal
line-art style fits the site's restrained aesthetic better than a filled
icon set. The visible icon represents the *destination* state (clicking it
switches to that state): moon + `aria-label="Switch to dark theme"` while
in light mode, sun + `aria-label="Switch to light theme"` while in dark
mode.

**7. Already-authenticated visitors hitting `/login`: no redirect.**

Pre-existing behavior (neither current `/login` nor `/register` redirects
an authenticated visitor away) is left unchanged. Out of scope for this
change — not something it set out to fix.

**8. Beta badge gets a hover state; register form gets no confirm-password
field.**

Now that `.beta-badge` is a real link, it needs a hover state or a
clickable element with zero visual feedback reads as broken — reuse the
existing `.origami-button-secondary` hover pattern (`var(--og-accent-fill)`
background swap) rather than inventing a new one. Conversely, the register
form stays at email + password only (no confirm-password field): the
backend API takes a single password and adding client-side confirmation is
a real UX improvement but new scope this change didn't set out to make.

**9. Combined-page layout: Login first (top on mobile, left on desktop),
Register second, each with its own heading.**

Desktop: two columns, Login left / Register right. Mobile (stacked):
Login above Register, matching Login's status as the more common action
and its current prominence as the primary nav entry point. Each form gets
its own heading ("Log in" / "Register") since two unlabeled forms side by
side on one page is genuinely ambiguous — the page's overall `<h1>`
becomes "Log in or register".

**10. Nav wraps onto two lines on narrow viewports; no hamburger menu.**

`.origami-world nav` currently has no `flex-wrap`, so items already
overflow/squish on narrow screens — worse once the theme toggle (wider
than a text link) is added. Fix: `flex-wrap: wrap` plus two flex groups
(left: Home/Workspaces/Beta; right: toggle + Login-or-Register, with
`margin-left: auto`), so the right group wraps to its own line instead of
squishing. No hamburger menu — that's new infrastructure this codebase
doesn't have anywhere, out of scope for this change.

**11. `DESIGN.md`'s component catalogue is updated alongside the code.**

Add a "Theme Toggle" entry and update the existing "Beta Mark" entry to
note it's now interactive (a link, with a hover state). `DESIGN.md` is
this repo's documented source of truth for the design system — shipping a
new reusable component without cataloguing it lets the doc drift out of
date.

## Risks / Trade-offs

- **[Risk] Removing `/register` breaks any external link or bookmark
  pointing at it.** → Accepted per explicit product decision; the app is
  pre-beta with limited external linking, and `/login` is one click away in
  the new combined page.
- **[Risk] Attribute-selector CSS override needs care to avoid specificity
  fights with the existing media query.** → Mitigate by keeping the
  attribute selectors at the same specificity level (`html[data-theme="x"]
  .origami-world { ... }`) and placing them after the media query in file
  order, and by testing all three states (no attribute + light OS, no
  attribute + dark OS, explicit override in both directions).
- **[Trade-off] Theme preference doesn't follow the user across devices**
  (localStorage only). Acceptable per explicit product decision to avoid
  backend/DB scope; can be revisited as a follow-up if needed.
- **[Risk] Vendoring Lucide's SVGs by hand (copy-paste, not a package
  dependency) means no automatic update path if Lucide changes its icon
  paths.** → Acceptable: this mirrors how `alpine.min.js`, `purify.min.js`,
  and `marked.min.js` are already vendored — a manual, deliberate update is
  the established pattern here, not an oversight.

## Migration Plan

Frontend-only, no data migration, no backend deploy required. Ship as a
single change: update `nav.html`, `style.css`, merge `login/index.html`,
delete `register/`. No feature flag — old and new nav can't coexist
meaningfully (it's the same file), so this ships atomically like the prior
beta-badge and htmx→Alpine changes.

## Open Questions

None outstanding. All decisions above — including icon source and meaning,
authenticated-visitor redirect behavior, Beta badge hover state,
combined-page form order/headings, register form scope, mobile nav
wrapping, and the `DESIGN.md` catalogue update — were confirmed in a
`/grilling` session on this proposal before implementation.
