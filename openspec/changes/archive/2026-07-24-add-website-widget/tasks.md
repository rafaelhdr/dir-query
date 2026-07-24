## 1. Backend: `has_owner` field

- [x] 1.1 Add `has_owner: bool` to `WorkspacePublic` in `backend/app/schemas.py`
- [x] 1.2 Compute `has_owner = workspace.owner_user_id is not None` in
      `_workspace_public()` in `backend/app/api/workspaces.py`, alongside the
      existing `can_edit` computation
- [x] 1.3 Add/extend tests in `backend/tests/test_workspaces.py` covering
      `has_owner: true` for an owned workspace and `has_owner: false` for an
      ownerless one, for both the owner's own request and another viewer's
      request

## 2. Backend: CORS

- [x] 2.1 Add `CORSMiddleware` in `backend/app/main.py`'s `create_app()` with
      `allow_origins=["*"]`, `allow_credentials=False`, permissive methods/headers
      for `GET`/`POST`
- [x] 2.2 Add a test asserting a cross-origin request (e.g. an `Origin` header
      from an arbitrary third-party value) to `GET /api/workspaces/{slug}` and
      `POST /api/w/{slug}/ask` receives `Access-Control-Allow-Origin: *`

## 3. Frontend: widget script (`frontend/public/widget.js`)

- [x] 3.1 Create `frontend/public/widget.js`: on load, read `data-workspace` and
      `data-position` off its own `<script>` tag (via
      `document.currentScript`), defaulting `data-position` to `bottom-right`
      for missing/unrecognized values
- [x] 3.2 Inject a floating launcher bubble into the host page at the
      resolved position, with inline/scoped styles (neutral colors, no
      dependency on the host page's stylesheet) so it renders consistently
      regardless of the embedding site
- [x] 3.3 On launcher click, open a chat panel that fetches the workspace's
      name from `GET /api/workspaces/{slug}` (using the script's own origin,
      derived from its `src`) and displays it
- [x] 3.4 Implement question submission in the panel against
      `POST /api/w/{slug}/ask`, reusing the same SSE streaming/rendering
      approach as `frontend/public/w/ask/index.html` (loading state, streamed
      markdown-rendered answer via `marked` + `DOMPurify`, sources)
- [x] 3.5 Retain the `conversation_id` from the first answered exchange for
      the lifetime of the page load and include it on subsequent questions in
      the same session; do not persist it across reloads
- [x] 3.6 Add a small "Powered by Dir Query" link inside the opened panel,
      pointing at the widget's origin
- [x] 3.7 Style the launcher and panel with a neutral, minimal look distinct
      from the site's own Origami Geometric direction

## 4. Frontend: ask page button and modal

- [x] 4.1 In `frontend/public/w/ask/index.html`, add a "Make a widget for your
      website" button next to "See past conversations", visible to any
      visitor
- [x] 4.2 Add a `<dialog>` modal, styled consistent with the ask page's
      existing Origami Geometric direction, opened via `showModal()` on
      button click
- [x] 4.3 In the modal, render the `<script>` snippet text using
      `window.location.origin` and the current workspace's slug, with
      `data-position="bottom-right"` as the generated default
- [x] 4.4 Add a "Copy to clipboard" button using `navigator.clipboard.writeText`
      with a brief "Copied!" confirmation state
- [x] 4.5 Show the no-owner warning inside the modal when the already-fetched
      workspace's `has_owner` is `false`; keep it hidden when `true`

## 5. Verification

- [x] 5.1 Run backend test suite and confirm the new/updated tests pass
- [x] 5.2 Manually embed the generated snippet on a throwaway local HTML file
      served from a different origin/port than the app, and confirm the
      launcher appears, opens, answers a question, and handles a follow-up
      question in the same session
- [x] 5.3 Manually verify the modal's warning appears for an ownerless
      workspace and is absent for an owned one

## 6. Frontend: inline embed mode in `widget.js`

- [x] 6.1 Read `data-mode` (`widget` default, or `inline`) and, for inline
      mode, `data-target` (a container element id) off the script tag,
      alongside the existing `data-workspace`/`data-position` reads
- [x] 6.2 Refactor the panel-mounting step so building the chat panel DOM,
      fetching the workspace name, submitting questions, streaming/rendering
      answers, sources, conversation-id continuity, and the "Powered by Dir
      Query" footer are shared code paths, not duplicated per mode
- [x] 6.3 In widget mode (unchanged), mount the panel hidden inside the
      floating-launcher shadow host, revealed on launcher click
- [x] 6.4 In inline mode, attach a shadow root directly to the `data-target`
      container (falling back to a clear console error and no-op if the
      target id doesn't resolve to an element), mount the panel visible
      immediately with no launcher bubble, and size it to fill the container
      (100% width/height) rather than the fixed widget-mode panel dimensions

## 7. Frontend: ask page modal mode selector

- [x] 7.1 In `frontend/public/w/ask/index.html`'s widget modal, add a radio
      button group ("Widget" / "Inline"), defaulting to "Widget"
- [x] 7.2 Update the `widgetSnippet` getter so it generates
      `data-position="bottom-right"` when "Widget" is selected, or
      `data-mode="inline" data-target="dirquery-widget"` (plus a suggested
      `<div id="dirquery-widget"></div>` line above the script tag in the
      snippet text) when "Inline" is selected
- [x] 7.3 Confirm the displayed snippet updates immediately when the radio
      selection changes, without needing to reopen the modal

## 8. Verification: inline mode

- [x] 8.1 Manually embed the inline-mode snippet on a throwaway local HTML
      file served from a different origin/port than the app, and confirm no
      floating launcher appears, the panel is visible immediately inside the
      target container, and it answers a question plus a follow-up in the
      same session
- [x] 8.2 Manually verify switching the modal's radio button between
      "Widget" and "Inline" updates the visible snippet text accordingly
