## Context

The frontend (`frontend/public/`) is static HTML, no build step, served by Nginx with SSI includes for shared partials (`ssi on;` in `frontend/nginx.conf`). htmx is vendored locally at `frontend/public/htmx.min.js` and included once, via `partials/head.html`, into all 11 pages.

A full-repo audit found htmx's actual usage is limited to three forms — `login`, `register`, `workspaces/new` — each using `hx-post`/`hx-swap="none"` plus a `htmx:afterRequest` listener that manually `JSON.parse`s the response and does session-setup/redirect or error display. `auth.js` has one `htmx:configRequest` listener that injects the bearer token into htmx requests; the same file's `Auth.fetch` wrapper already does the equivalent for plain `fetch()`. Every other dynamic page (`workspaces/index.html`, `w/feed/files/index.html`, `w/ask/conversations/index.html`, `w/ask/index.html`) already uses plain `fetch()` + hand-rolled DOM building, with no htmx involvement at all. No other `hx-*` attributes, `htmx:*` events, or htmx-specific CSS classes exist anywhere in the repo.

An earlier evaluation considered `htmx-json` (a third-party htmx extension for declarative JSON binding) as a way to reduce that hand-rolled DOM code without changing the request/response shape. It was rejected: unlicensed, ~31 stars, last pushed months ago, no official htmx.org backing. Alpine.js was chosen instead: MIT-licensed, ~32k stars, pushed within the last week, and — like htmx — ships a single vendorable script with no build step, so it fits the repo's existing "framework-free, buildless" frontend convention while giving every page (not just the 3 forms) a shared declarative-binding pattern.

## Goals / Non-Goals

**Goals:**
- Remove htmx entirely (script, attributes, event listeners) with zero behavior change to any page.
- Replace the hand-rolled `fetch()` + manual DOM-building code on `workspaces/index.html`, `w/feed/files/index.html`, `w/ask/conversations/index.html`, and `w/ask/index.html` with Alpine's declarative bindings, reducing the amount of imperative JS app-wide, not just on the 3 htmx-driven forms.
- Preserve the existing sanitize-before-render pattern (`marked.parse()` → `DOMPurify.sanitize()` with the current allowlist, plus the link-hardening hook) exactly, on every page that renders markdown.
- Preserve `Auth.fetch` as the single, unchanged token-injection mechanism for every request app-wide.
- Keep the frontend buildless and vendored (no CDN, no bundler), consistent with `AGENTS.md`'s existing constraint.

**Non-Goals:**
- No JS build toolchain (bundler, transpiler, package manager) — Alpine is vendored as a single minified file, same as htmx/marked/DOMPurify today.
- No SPA-style client-side routing beyond the `window.history.replaceState` calls `w/ask/index.html` already makes.
- No CSS or visual redesign.
- No change to `partials/nav.html`'s hand-rolled login/logout script. It renders once per page load and logout does a full `window.location.reload()` rather than updating state in place, so there's little to gain from converting it; left as a follow-up (see Open Questions).
- No backend changes. All three forms already need to submit `multipart/form-data` (the backend's `/auth/login`, `/auth/register`, and `POST /workspaces` endpoints take `Form(...)` params, not JSON) — the Alpine replacement keeps using `FormData`, unchanged from what htmx was already sending.

## Decisions

**Vendor Alpine's self-initializing `cdn.min.js` build, pinned to an exact version, as `frontend/public/alpine.min.js`.** This is the build Alpine's own docs pair with a plain `<script defer>` tag and is the direct counterpart to how `htmx.min.js` self-registers today. Pinning to an exact version (not `@3`) keeps the vendored file reproducible, matching how `marked.min.js`/`purify.min.js` are already pinned. Alpine's `cdn.min.js` has no embedded version string (unlike the other three vendored libraries), so a one-line header comment recording version/source/date is added to the file at vendor time.

**Add `defer` to Alpine's script tag; this is a functional requirement, not a style preference.** Alpine's `cdn.min.js` calls `Alpine.start()` as soon as it executes, and that call does a one-time synchronous scan of the DOM for `x-data` roots — it only picks up later DOM changes via a `MutationObserver`. `partials/head.html` is included at the top of every page's `<head>` via SSI, so a non-deferred script would execute before `<body>` exists, and the initial scan would find zero components. `defer` delays execution until the document is fully parsed, guaranteeing every page's `x-data` roots exist by the time Alpine scans. htmx has no equivalent load-order requirement, which is why the existing script tag has no `defer`.

**`Auth.fetch` becomes the sole request/token-injection mechanism app-wide, replacing `auth.js`'s `htmx:configRequest` listener.** Every page already either uses `Auth.fetch` directly or will after this migration (the 3 forms currently rely on htmx's own request path); consolidating onto one mechanism removes a whole class of "did I remember to attach the token" bugs across two different request pathways.

**Introduce one shared `window.apiForm()` Alpine factory in `auth.js`** (rather than repeating request/error/submitting logic three times) for `login`, `register`, and `workspaces/new`, since all three forms share the exact same submit → parse-JSON → set-session-or-show-error shape. `workspaces/new` composes this shared factory with its own page-local radio-toggle state (`Object.assign(apiForm(), {...})`) rather than duplicating the shared logic.

**On `w/ask/index.html`, keep the SSE frame-parsing loop, the 80ms render throttle, and the sanitize-then-render function as plain imperative JS; only the outer per-exchange state becomes Alpine-reactive.** The Streams API reader loop is inherently imperative and gains nothing from being forced into Alpine idioms. Each exchange becomes a reactive `{id, question, status, answerHtml, sources, errorMessage}` object; the streaming loop writes to these fields at the same ~12.5 Hz cadence it already renders at, so Alpine adds no new DOM-write frequency — `x-html="exchange.answerHtml"` performs the same single `innerHTML` write per throttled tick that the current code already does directly.

**Use `x-show`, never `x-if`, for the exchange's loading/streaming/answered/error branches.** `x-if` tears down and rebuilds its DOM subtree on every state transition; since the answer element accumulates content across the `loading` → `streaming` → `answered` transition via repeated `x-html` writes, using `x-if` would destroy and recreate that element mid-stream. `x-show` keeps the same DOM node alive for the exchange's whole lifetime, which is a direct, low-risk translation of what the code already does (it never removes the `bodyEl` node today either — it only replaces its contents).

**`renderMarkdown()` on both `workspaces/index.html` and `w/ask/index.html` changes from "sanitize and write directly to a container" to "sanitize and return a string," bound afterward via `x-html`.** The sanitize step itself (allowlist, `afterSanitizeAttributes` link-hardening hook) is copied through unchanged — only the last line changes from an `innerHTML` assignment to a `return`. `x-html` is bound exclusively to this already-sanitized string, never to raw markdown output, on both pages.

**No new capability spec for "frontend" or "Alpine.js."** `openspec/specs/` is organized per user-facing capability (`ask-page`, `document-management`, `user-auth`, …), not by implementation mechanism, and only one existing requirement (`user-auth`) names htmx explicitly. This migration changes *how* interactivity is implemented, not *what* any capability does, so it's recorded here in `design.md` plus a single delta to the `user-auth` spec's mechanism-describing wording, rather than inventing a new capability.

## Risks / Trade-offs

- **`w/ask/index.html` is the highest-risk file** — it combines SSE streaming, a render throttle, and XSS-sensitive sanitization. → Mitigated by migrating it last (after every lower-risk page has validated the overall approach), keeping its core parsing/throttle/sanitize logic byte-for-byte unchanged, and using the `x-show`-not-`x-if` rule above. Manual verification includes explicitly re-confirming the sanitizer strips a hostile payload after the change.
- **No frontend test suite or CI exists**, so every page's correctness rests on manual verification. → Each migrated page gets an explicit manual verification checklist in `tasks.md`, and the work is sequenced as independent, revertable per-page commits so a regression on one page doesn't block or entangle the others.
- **Unifying `w/ask/index.html`'s live-streaming and past-conversation-reload code paths onto one `{status, answerHtml, sources}` shape** risks silently dropping a field (e.g. `sources`) that one of the two previously-independent code paths handled correctly and the other didn't. → Flagged explicitly in `tasks.md` for extra scrutiny; verification checklist requires exercising both paths (fresh question and reloading a past conversation across all three exchange statuses).
- **Team unfamiliarity with Alpine's reactivity model** (Proxies, `x-data` scoping) vs. htmx's simpler request/response/swap model. → Mitigated by keeping the shared patterns few and consistent (one `apiForm()` factory, one `x-for`/`x-show` list pattern reused across four pages) rather than inventing a different idiom per page.

## Migration Plan

Each step is an independent, revertable static-asset change (no backend involvement, no data migration), sequenced low-risk-first:

1. Vendor `alpine.min.js`, wire it into `partials/head.html` (with `defer`), remove `auth.js`'s `htmx:configRequest` listener, add the shared `apiForm()` helper.
2. Migrate the 3 forms (`login`, `register`, `workspaces/new`).
3. Migrate `workspaces/index.html`.
4. Migrate `w/ask/conversations/index.html`.
5. Migrate `w/feed/files/index.html`.
6. Migrate `w/ask/index.html` (last, highest risk).
7. Delete `htmx.min.js`; final repo-wide grep for `htmx`/`hx-` to confirm zero remaining references before removal.
8. Update `AGENTS.md`.
9. Sync the `user-auth` delta spec and archive this change.

No rollback tooling is needed beyond standard git revert, since every change is a static frontend asset with no persisted-state implications.

## Open Questions

- Should `partials/nav.html`'s hand-rolled login/logout DOM building also move to Alpine? Deferred — see Non-Goals. Worth a follow-up change if/when that script grows more logic.
- Should `w/ask/index.html`'s question `<input>` become `x-model`-bound, or stay read via `new FormData(event.target)` as it is today? Either is acceptable; left to the implementer's judgment during task execution rather than mandated here, since it doesn't affect the streaming/sanitization design above.
