## Context

The frontend is static HTML + htmx with no build step (see AGENTS.md);
shared markup is assembled at request time via Nginx SSI includes from
`frontend/public/partials/`. The ask and upload pages
(`frontend/public/w/ask/index.html`,
`frontend/public/w/feed/upload/index.html`) each currently render a
generic `page_heading` ("Ask" / "Upload") via the shared
`partials/heading.html` include, and route matching in
`frontend/nginx.conf` only recognizes `/w/<slug>/ask` and
`/w/<slug>/feed/upload` — there is no route for the bare `/w/<slug>`
workspace URL. Neither page currently knows the workspace's name; both
only read the `<slug>` segment out of `window.location.pathname`.

## Goals / Non-Goals

**Goals:**
- Show the workspace's name (not a generic label) as the `<h1>` on both
  the ask and upload pages.
- Give both pages a shared tab bar (Ask / Upload) for switching between
  them, with the current page's tab marked selected.
- Make `/w/<slug>` resolve to the ask page with its Ask tab selected.

**Non-Goals:**
- No new backend endpoints — the existing `GET /api/workspaces/{slug}`
  is sufficient to fetch the workspace name.
- No introduction of a JS build toolchain or client-side router.
- No changes to the ask/upload forms' own behavior.

## Decisions

- **Fetch the workspace name client-side, not via SSI.** SSI runs
  entirely on Nginx and cannot call the backend API, so the workspace
  name can't be injected at include-time the way `page_heading` is
  today. Both pages already fetch `slug` from the URL and make a
  `fetch()` call on load (`/ask` or `/uploads`); adding a
  `GET /api/workspaces/{slug}` call on `DOMContentLoaded` follows the
  same pattern. The heading partial's static text becomes a target
  `<h1 id="workspace-name">` that this fetch populates.
- **Keep `partials/heading.html` for the beta badge, drop
  `page_heading` from these two pages.** Both pages already override
  the page title via `page_title`; replacing `page_heading`'s static
  text with a `workspace-name` placeholder in a small per-page
  `<h1>` (populated by JS) is simpler than teaching SSI about dynamic
  values, and it keeps the shared beta-badge markup.
- **Duplicate the tab bar markup in both pages rather than adding a new
  SSI partial.** Two tabs, two files — an SSI partial would need a
  parameter for "which tab is active," which SSI doesn't support
  cleanly (no conditionals). Plain duplicated HTML (one `<nav
  class="workspace-tabs">` block per page, with the active tab's link
  carrying an `aria-current="page"` / `.active` class already baked
  into the static markup) is simpler and consistent with this
  project's static-first approach.
- **Route `/w/<slug>` to the same `w/ask/index.html` file used for
  `/w/<slug>/ask`.** Mirrors the existing `try_files ... /w/ask/index.html`
  pattern already used for the `/ask` route in `nginx.conf`, so the ask
  page's own client-side JS (which derives `slug` from
  `pathname.split("/")[2]`) keeps working unchanged for both URLs.
- **Remove the inline "Upload more documents" / "Ask a question" text
  links.** The tab bar replaces them; keeping both would be redundant
  navigation to the same destination.

## Risks / Trade-offs

- [Workspace name fetch fails or is slow] → Fall back to showing the
  slug (already known synchronously from the URL) as a placeholder
  `<h1>` text until the fetch resolves or errors, so the heading is
  never blank.
- [Duplicated tab bar markup drifts between the two pages over time] →
  Small, stable UI (two links); acceptable given no build tooling
  exists to share it more cleanly without adding complexity.
- [Nonexistent workspace slug hit via bare `/w/<slug>`] → Same as
  today's `/ask` page: the workspace-name fetch to
  `GET /api/workspaces/{slug}` returns 404, and the page shows that
  error state instead of a name (existing `ask-page` error-handling
  patterns extend naturally to this fetch).

## Migration Plan

No data migration. Deploy is a static-asset + Nginx config change:
update `frontend/nginx.conf` to add the `/w/<slug>` route, update both
page HTML files. No rollback complexity beyond reverting these files.

## Open Questions

None.
