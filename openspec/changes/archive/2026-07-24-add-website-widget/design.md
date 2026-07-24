## Context

The ask page (`frontend/public/w/ask/index.html`) already lets a
visitor ask questions against a workspace and stream answers from
`POST /api/w/{slug}/ask`, backed by the `question-answering` capability.
Workspace ownership is optional (`workspace-management`): a workspace
created while logged out has no owner and stays public and editable by
anyone; the backend never reveals owner identity, only a computed
`can_edit` boolean.

There is no existing modal component, no clipboard-copy code, no
cross-origin (CORS) configuration, and no concept of an "embeddable"
surface anywhere in this codebase today — the frontend is plain
Alpine.js served statically by Nginx, and the backend is a FastAPI app
with no `CORSMiddleware` registered. This is the first feature that
needs the backend to be called from a page not served by this
deployment.

## Goals / Non-Goals

**Goals:**
- Let any visitor to a workspace's ask page generate a copy-pasteable
  `<script>` snippet that embeds a live Q&A widget for that workspace
  on a third-party site.
- Support two embed modes from that same snippet-generation flow: a
  floating "Widget" launcher, and an "Inline" panel that sits directly
  in the embedder's own page layout instead of floating over it —
  chosen via a radio button in the modal.
- Warn when the embedded widget depends on a workspace that could be
  removed by a future cleanup job (i.e. has no owner), without
  revealing anything about ownership beyond that fact.
- Keep the widget's own visual footprint on the host page neutral, so
  it doesn't look out of place dropped into an arbitrary site's design.

**Non-Goals:**
- Restricting which origins may embed a given workspace (no
  per-workspace allowed-origins list). Any site that has the snippet
  can embed it, same as anyone can already open the ask page directly.
- Building a color/style picker in the modal. Visual customization, if
  any, is limited to hand-editable attributes on the snippet itself.
- Distinguishing widget-originated conversations from directly-asked
  ones anywhere in the UI or data model.
- The cleanup job that removes ownerless workspaces — out of scope,
  referenced only to justify the warning copy.

## Decisions

### Widget mechanism: script tag injecting the panel, not an iframe
An `<iframe src=".../w/{slug}/ask">` would have been simpler (no CORS,
no new JS bundle) but always renders as a fixed boxed panel wherever
it's placed — it can't become a floating launcher, and it would need a
second, differently-configured iframe for inline mode anyway. A
`<script>` tag that injects its own DOM gives both the common
floating-launcher chat pattern (Intercom/Crisp-style) in widget mode
*and* an on-page panel in inline mode, from the same delivery
mechanism, positioning itself via CSS independent of the host page's
layout.

### Two embed modes, one script, signaled by data attributes
The script tag carries `data-mode` (`widget`, the default, or
`inline`) and, for inline mode, `data-target` (the id of a container
element already on the host page). `widget.js` reads these once at
load and branches only on *how the chat panel gets mounted*: widget
mode creates a floating launcher that reveals the panel on click;
inline mode mounts the panel directly into the `data-target` container,
visible immediately, sized to fill it. Every other behavior — fetching
the workspace name, submitting questions, streaming/rendering answers,
conversation-id continuity, sources, the "Powered by Dir Query"
footer, and the neutral visual style — is identical code shared by
both modes, since none of it depends on how the panel is mounted. This
avoids shipping two separate scripts (double the surface to maintain
for embedders and for this codebase) for what is, functionally, a
single option among many the panel's container could have.

### Snippet-driven origin resolution
The snippet's `src` uses `window.location.origin` captured at the
moment the modal is generated (not a hardcoded domain), so the same
code works correctly across any self-hosted deployment (dev, staging,
a user's own instance) without configuration.

### CORS: wildcard origin, no credentials
`CORSMiddleware(allow_origins=["*"], allow_credentials=False)` is
added at the app level. This necessarily applies to every route, not
just the widget-relevant ones — FastAPI's CORS handling is
app-scoped — but that's acceptable because:
- The workspace-detail and ask endpoints the widget calls are already
  unauthenticated and public.
- Auth in this app is a bearer token read from `localStorage` (see
  `frontend/public/auth.js`), not a cookie. A third-party origin has
  no way to read another origin's `localStorage`, so it cannot forge
  an authenticated request even though the response headers now permit
  cross-origin reads. `allow_credentials=False` also blocks the one
  credentialed-CORS combination that could matter (cookies), which
  this app doesn't use anyway.
An alternative — a per-workspace allowed-origins allowlist enforced
server-side — was rejected as disproportionate scope for a first
version (see Non-Goals) and deferred to a future change if abuse
becomes a real concern.

### `has_owner` field instead of reusing `can_edit`
`can_edit` is `true` both when a workspace has no owner and when the
current viewer *is* the owner — it can't distinguish those two cases
from the client alone, which is exactly what the modal's warning needs
to distinguish. A new `has_owner: bool` (`owner_user_id is not None`)
is added alongside `can_edit`, computed identically for every viewer
regardless of their own identity, and reveals only *whether* an owner
exists — never who it is, preserving the existing "no owner identity
in responses" guarantee from `workspace-management`.

### Widget conversations are ordinary conversations
The widget calls the same `POST /api/w/{slug}/ask` the main ask page
uses, with no new parameter marking the request's origin. Conversations
it creates are stored and listed exactly like any other — simplest
option, and avoids adding a field to the conversation/exchange schema
for a distinction nobody asked to see.

### Widget visual style: neutral, not the site's Origami Geometric direction
The rest of the site uses a specific branded direction (paper/ink
neutrals, one coral accent, fold-cut corners, Poppins). Carrying that
onto arbitrary third-party sites would clash with whatever design
those sites already have. The chat panel instead uses a minimal, low-
contrast default (system font stack, greyscale/neutral accent) in both
embed modes, with only layout attributes (`data-position` in widget
mode; `data-mode`/`data-target` to choose the mode itself) exposed on
the snippet in this version; further style knobs (e.g. an accent color
attribute) are easy to add later without changing the delivery
mechanism, but are not built now since the modal itself won't expose
any configuration UI for them beyond the mode choice.

### Modal implementation: native `<dialog>`
No modal primitive exists anywhere in this codebase yet. A native
`<dialog>` element (`showModal()`/`close()`) is used rather than a
hand-rolled overlay `<div>`, since it gets focus trapping, `Esc`-to-
close, and top-layer stacking for free, matching the "no build step,
minimal JS" ethos of the rest of the frontend. The modal is styled
consistent with the site's own Origami Geometric direction (unlike the
widget it generates) — it's chrome belonging to this site, not to the
embedding host page.

## Risks / Trade-offs

- **[Risk]** Wildcard CORS technically permits cross-origin reads of
  every endpoint, including ones not related to the widget (e.g. the
  workspace list). → **Mitigation**: every endpoint reachable this way
  was already unauthenticated and public before this change; nothing
  newly sensitive becomes reachable. Mutating/authenticated endpoints
  still require a bearer token that a third-party origin cannot obtain
  from `localStorage`.
- **[Risk]** Because any visitor can generate a widget snippet for any
  workspace (no ownership gating), someone could embed a workspace
  they don't own on their own site. → **Mitigation**: this mirrors the
  existing trust model — the ask page itself is already fully public
  and unauthenticated for any slug; the widget doesn't expose anything
  the direct ask page didn't already expose.
- **[Risk]** An ownerless workspace referenced by an embedded widget
  could be cleaned up later (future, out-of-scope job), silently
  breaking the widget on whatever site it's embedded on. →
  **Mitigation**: the modal's warning is the whole point — it tells
  the person embedding it, at generation time, that this can happen.
  No runtime detection/handling of a since-deleted workspace is
  attempted; the widget simply fails to load, same as visiting a
  deleted workspace's ask page directly would.

## Migration Plan

No data migration is needed beyond a new nullable-safe computed field
(`has_owner`) derived from an existing column. Rollout is a single
deploy: backend (CORS middleware + schema field) and frontend (new
button/modal + new `widget.js` static file) ship together; there's no
sequencing dependency between them beyond both being present before
any snippet is generated and used. Rollback is a plain revert — no
persisted state depends on this change.

## Open Questions

None outstanding — access model, CORS approach, widget mechanism,
conversation-history behavior, and visual style were all resolved with
the requester before this design was written.
