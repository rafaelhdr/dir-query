## Why

htmx's actual footprint in this frontend is narrow: only three forms (login, register, workspaces/new) use `hx-post`/`hx-swap="none"` plus a `htmx:afterRequest` listener, while every other dynamic page (workspaces list, files list, ask, past conversations) already hand-rolls `fetch()` + manual DOM building without htmx at all. htmx is doing too little to earn its keep on the pages that use it, and the rest of the app pays full boilerplate cost for JSON-driven rendering with no library help. Consolidating on Alpine.js — a small, actively maintained, MIT-licensed declarative library that binds directly to JSON responses without requiring the server to return HTML — removes htmx entirely and lets every dynamic page share one lightweight pattern instead of two disjoint ones.

## What Changes

- Vendor Alpine.js locally at `frontend/public/alpine.min.js` (pinned version, no CDN), matching the existing no-build-step convention used for `htmx.min.js`/`marked.min.js`/`purify.min.js`.
- **BREAKING**: Remove `frontend/public/htmx.min.js` and its inclusion in `frontend/public/partials/head.html`; swap in the Alpine `<script>` tag (with `defer`, required for Alpine's self-initializing boot sequence).
- Remove `auth.js`'s `htmx:configRequest` listener (dead code once no `hx-*` requests exist); `Auth.fetch` becomes the sole request/token-injection mechanism app-wide. Add a shared `window.apiForm()` Alpine helper to `auth.js` for the three auth/workspace forms to reuse.
- Rewrite `login/index.html`, `register/index.html`, and `workspaces/new/index.html` onto Alpine (`x-data`, `@submit.prevent`, `x-text`, `x-show`/`x-model` for the existing dedicated-API-key radio toggle), replacing their `hx-post`/`htmx:afterRequest` plumbing.
- Rewrite `workspaces/index.html` and `w/ask/conversations/index.html` onto Alpine `x-for`/`x-show` list rendering, replacing their hand-rolled `renderConversations()`/list-building JS.
- Rewrite `w/feed/files/index.html` onto Alpine `x-for`, including a per-row `x-show`-toggled inline-rename pattern, replacing `renderFiles()`/`renderNameCell()`/`renderNameEditor()`.
- Rewrite `w/ask/index.html`'s outer state (exchange list, loading/streaming/answered/error status, new-conversation visibility) onto Alpine `x-for`/`x-show`, while leaving the SSE frame-parsing loop, the 80ms render throttle, and the sanitize-before-render (`marked` → `DOMPurify`) pattern unchanged in behavior.
- Update `AGENTS.md`'s frontend-development section and repo-layout references from htmx to Alpine.js.

## Capabilities

### New Capabilities

None. This change replaces an implementation mechanism (htmx → Alpine.js); it does not add or change what any user-facing capability does.

### Modified Capabilities

- `user-auth`: the "frontend attaches the stored token to API requests" requirement currently describes token attachment as covering "both htmx-driven and script-driven" requests. Post-migration there is a single mechanism (`Auth.fetch`, used by every page including the three forms), so this wording is no longer accurate and needs to be updated. The requirement's behavior and all of its scenarios are unchanged — only the description of the underlying mechanism changes.

## Impact

- **New file**: `frontend/public/alpine.min.js`
- **Removed file**: `frontend/public/htmx.min.js`
- **Modified**: `frontend/public/partials/head.html`, `frontend/public/auth.js`, `frontend/public/login/index.html`, `frontend/public/register/index.html`, `frontend/public/workspaces/new/index.html`, `frontend/public/workspaces/index.html`, `frontend/public/w/ask/conversations/index.html`, `frontend/public/w/feed/files/index.html`, `frontend/public/w/ask/index.html`, `AGENTS.md`
- No backend changes, no API changes, no data migration. All affected forms already submit `multipart/form-data`, which FastAPI's `Form(...)` endpoints already accept — the migration does not change request payload shape.
- No frontend test suite/CI exists; verification for every affected page is manual (`docker compose up --build` / `docker compose watch` + browser checks).
