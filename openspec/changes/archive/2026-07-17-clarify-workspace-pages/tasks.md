## 1. Routing

- [x] 1.1 Add a route in `frontend/nginx.conf` matching `/w/[^/]+/?$` that
      serves `w/ask/index.html` (mirroring the existing `/ask` route
      pattern), so the bare workspace URL resolves to the ask page.

## 2. Ask page (`frontend/public/w/ask/index.html`)

- [x] 2.1 Replace the `page_heading`/`partials/heading.html` include with
      a page-local `<h1 id="workspace-name">` (still wrapped with the
      beta badge) that initially shows the slug as a placeholder.
- [x] 2.2 Add a tab bar (`<nav class="workspace-tabs">`) with "Ask" and
      "Upload" links, the "Ask" tab marked selected
      (e.g. `aria-current="page"` + `.active` class), linking to
      `/w/<slug>/ask` and `/w/<slug>/feed/upload` respectively.
- [x] 2.3 Remove the inline "Upload more documents" paragraph link (now
      redundant with the tab bar).
- [x] 2.4 On page load, fetch `GET /api/workspaces/<slug>` and set the
      `<h1>` text to the returned `name`; on a 404 or error response,
      show a "workspace not found" state instead of a name.

## 3. Upload page (`frontend/public/w/feed/upload/index.html`)

- [x] 3.1 Replace the `page_heading`/`partials/heading.html` include with
      a page-local `<h1 id="workspace-name">` (still wrapped with the
      beta badge) that initially shows the slug as a placeholder.
- [x] 3.2 Add the same tab bar as the ask page, with the "Upload" tab
      marked selected, linking to `/w/<slug>/ask` and
      `/w/<slug>/feed/upload`.
- [x] 3.3 Remove the inline "Ask a question" paragraph link (now
      redundant with the tab bar).
- [x] 3.4 On page load, fetch `GET /api/workspaces/<slug>` and set the
      `<h1>` text to the returned `name`; on a 404 or error response,
      show a "workspace not found" state instead of a name.

## 4. Styling

- [x] 4.1 Add `.workspace-tabs` styles to `frontend/style.css` (tab
      layout, selected-tab visual state), consistent with the existing
      minimal styling.

## 5. Verification

- [x] 5.1 Manually verify: `/w/<slug>`, `/w/<slug>/ask`, and
      `/w/<slug>/feed/upload` all show the workspace's name in the
      heading and the correct tab selected.
- [x] 5.2 Manually verify: clicking the Upload tab from the ask page and
      the Ask tab from the upload page navigates correctly.
- [x] 5.3 Manually verify: visiting any of the three URLs for a
      nonexistent slug shows a "workspace not found" state instead of a
      blank or broken heading.
