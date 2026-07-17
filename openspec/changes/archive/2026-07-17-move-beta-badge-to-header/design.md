## Context

The frontend is static HTML + htmx with no build step; shared markup is
assembled at request time via Nginx SSI includes from
`frontend/public/partials/`. The beta badge (`<span class="beta-badge">Beta</span>`)
today lives in three places, all inside page content:

- `frontend/public/partials/heading.html` — appended after the `<h1>` text,
  included by the home/workspaces pages.
- `frontend/public/w/ask/index.html` — duplicated inline in that page's own
  `<h1>`.
- `frontend/public/w/feed/upload/index.html` — same duplication.

This placement was a deliberate choice recorded in the archived
`clarify-workspace-pages` design doc ("keep `partials/heading.html` for the
beta badge"). Revisiting it: beta status isn't part of any page's content —
it's a persistent, app-wide fact about the product. The site header
(`partials/nav.html`) is already included on every page that currently
shows the badge, so it's a better structural home and removes the need to
duplicate the badge markup across `w/ask` and `w/feed/upload`.

## Goals / Non-Goals

**Goals:**
- Show the beta badge exactly once per page, in the header, instead of in
  page content headings.
- Eliminate the duplicated badge markup currently repeated in
  `w/ask/index.html` and `w/feed/upload/index.html`.
- Preserve the badge's current visual style (`.beta-badge` in
  `frontend/public/style.css`).

**Non-Goals:**
- No change to the badge's text or styling itself.
- No new pages, endpoints, or capabilities.
- No change to which pages show the badge — every page that includes
  `partials/nav.html` today already includes `partials/heading.html` (or
  its own duplicated badge), so coverage is unchanged.

## Decisions

- **Add the badge markup directly to `partials/nav.html`, not a new
  partial.** Nav is already a single shared include present on every
  affected page; introducing a separate "header" partial would add an
  extra include with no benefit, since nav and header are the same
  concept in this codebase.
- **Remove the badge from `partials/heading.html` entirely rather than
  making it conditional.** The heading partial's only remaining job
  becomes rendering the page's `<h1>` text — no page needs the badge in
  content once it's in the header.
- **De-duplicate `w/ask/index.html` and `w/feed/upload/index.html`.** Both
  currently hardcode `<span class="beta-badge">Beta</span>` next to their
  dynamic `workspace-name` span because they don't use the shared heading
  partial. Once the badge lives in nav, both pages simply drop that span
  and keep only the `workspace-name` heading — no behavior change to the
  workspace-name fetch/JS.
- **Reuse the existing `.beta-badge` CSS class as-is.** Only add layout
  CSS (e.g., wrapping nav's links and the badge in a flex container with
  spacing) if visual inspection in the browser shows it doesn't already
  sit reasonably next to the nav links.

## Risks / Trade-offs

- [Badge might visually crowd the nav links on narrow viewports] →
  Verify in the browser after implementation; add a small flex-wrap or
  margin adjustment in `style.css` if needed, without changing
  `.beta-badge` itself.
- [Spec text for "Home page discloses beta status" currently ties the
  requirement to the home page specifically] → Update via the accompanying
  spec delta to describe header placement and app-wide visibility, so the
  spec matches actual behavior (badge has always rendered on every page,
  not just home).

## Migration Plan

No data migration. Deploy is a static-asset change: update
`partials/nav.html`, `partials/heading.html`, `w/ask/index.html`,
`w/feed/upload/index.html`, and `style.css` if needed. No rollback
complexity beyond reverting these files.

## Open Questions

None.
