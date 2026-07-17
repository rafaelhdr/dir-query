## 1. Move badge into the header

- [x] 1.1 Add `<span class="beta-badge">Beta</span>` to
      `frontend/public/partials/nav.html`, alongside the existing nav
      links.
- [x] 1.2 Remove `<span class="beta-badge">Beta</span>` from
      `frontend/public/partials/heading.html`, leaving only the
      `page_heading` echo.
- [x] 1.3 Remove the inline `<span class="beta-badge">Beta</span>` from
      the `<h1>` in `frontend/public/w/ask/index.html`, keeping the
      `workspace-name` span.
- [x] 1.4 Remove the inline `<span class="beta-badge">Beta</span>` from
      the `<h1>` in `frontend/public/w/feed/upload/index.html`, keeping
      the `workspace-name` span.

## 2. Verify and polish styling

- [x] 2.1 Run the app locally (`docker compose up --build`) and check the
      header on `/`, `/home`, `/workspaces`, `/workspaces/new`,
      `/w/<slug>/ask`, and `/w/<slug>/feed/upload`. (Browser extension
      unavailable in this session; verified via `curl` against the
      rebuilt container that the badge renders exactly once per page,
      inside `<nav>`.)
- [x] 2.2 Added a small flex layout to `nav` in
      `frontend/public/style.css` (`display: flex; align-items: center`)
      plus `margin-left: auto` on `nav .beta-badge` so it sits at the end
      of the header row, without changing the `.beta-badge` class itself.
- [x] 2.3 Confirmed via `curl` that the badge no longer appears in any
      page's `<h1>` content.

## 3. Sync specs

- [x] 3.1 Ran `opsx:sync` to apply the `specs/home-page/spec.md` delta to
      `openspec/specs/home-page/spec.md`.
- [x] 3.2 Archive the change once implementation and spec sync are
      verified.
