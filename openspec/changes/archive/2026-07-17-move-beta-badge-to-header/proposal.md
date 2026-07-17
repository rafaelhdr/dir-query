## Why

The beta badge currently renders inside each page's `<h1>` content heading
(`partials/heading.html`, and duplicated inline on the ask/upload workspace
pages). This was a deliberate choice recorded in the archived change
`clarify-workspace-pages` design doc. In practice, beta status is a
persistent, app-wide indicator — not something specific to any one page's
content — so it reads more naturally as part of the site header/nav
(`partials/nav.html`), which is already included on every page. This change
moves it there and reverses the prior "keep it in the heading" decision.

## What Changes

- Move the `.beta-badge` markup out of `partials/heading.html` and the
  inline `<h1>` on `w/ask/index.html` and `w/feed/upload/index.html`.
- Add the beta badge to the shared `partials/nav.html`, so it renders once
  in the header on every page instead of in each page's content heading.
- Adjust nav layout CSS only if needed so the badge sits cleanly alongside
  the nav links (no change to the `.beta-badge` style itself).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `home-page`: the "Home page discloses beta status" requirement is
  updated to specify that beta status is shown via the site header (not
  page content), and that this applies application-wide, not just on the
  home page.

## Impact

- `frontend/public/partials/nav.html` — add beta badge markup.
- `frontend/public/partials/heading.html` — remove beta badge markup.
- `frontend/public/w/ask/index.html` — remove inline beta badge from `<h1>`.
- `frontend/public/w/feed/upload/index.html` — remove inline beta badge
  from `<h1>`.
- `frontend/public/style.css` — minor layout adjustment only if needed.
- No backend changes, no new endpoints, no data migration.
