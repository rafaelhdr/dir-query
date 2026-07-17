## Why

Workspace pages currently give no visual confirmation of which workspace
you're in — the heading just says "Ask" or "Upload" — and moving between
a workspace's ask and upload pages relies on a single inline text link
buried in a paragraph. There's also no page at the bare workspace URL
(`/w/<slug>`), so users always land via a direct `/ask` or
`/feed/upload` link. This makes the workspace pages feel disconnected
and harder to navigate.

## What Changes

- The ask page and the upload page both show an `<h1>` with the
  workspace's name (not the generic "Ask" / "Upload" heading).
- Both pages get a tab bar with two tabs, "Ask" and "Upload", so a user
  can switch between them without hunting for a link. The tab for the
  current page is visually marked as selected.
- Opening the bare workspace URL (`/w/<slug>`) now serves the ask page
  by default, with its "Ask" tab selected.
- The existing inline "Upload more documents" / "Ask a question" text
  links are replaced by the tab bar (no more duplicate navigation).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `ask-page`: heading now shows the workspace's name instead of "Ask";
  navigation to the upload page is via a tab bar (replacing the inline
  text link); the bare `/w/<slug>` URL serves this page by default.
- `document-upload`: heading now shows the workspace's name instead of
  "Upload"; navigation to the ask page is via a tab bar (replacing the
  inline text link).

## Impact

- `frontend/public/w/ask/index.html`: add workspace-name heading, add
  tab bar, remove inline "Upload more documents" link.
- `frontend/public/w/feed/upload/index.html`: add workspace-name
  heading, add tab bar, remove inline "Ask a question" link.
- `frontend/nginx.conf`: add a route for the bare `/w/<slug>` path that
  serves the ask page.
- Both pages already fetch nothing about the workspace itself (only the
  slug from the URL) — showing the workspace's name requires calling
  `GET /api/workspaces/{slug}` on page load.
