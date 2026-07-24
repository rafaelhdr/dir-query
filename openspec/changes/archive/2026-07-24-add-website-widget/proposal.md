## Why

Workspace owners currently have no way to surface a workspace's Q&A
outside this site. Letting anyone generate a copy-pasteable embed
snippet from the ask page lets a workspace's question-answering be
placed directly on the owner's own website, without requiring any
backend configuration step first.

## What Changes

- Add a "Make a widget for your website" button on the ask page, next
  to "See past conversations", open to any visitor (no ownership
  check).
- The button opens a modal containing a radio choice between two embed
  modes — "Widget" (a floating launcher) and "Inline" (renders directly
  in the embedder's own page layout) — and a `<script>` snippet (with
  the current origin, the workspace's slug, and mode-specific
  attributes baked in) that updates to match whichever mode is
  selected, a "Copy to clipboard" button, and — only when the
  workspace has no owner — a warning that the embed may stop working
  if the workspace is later cleaned up.
- Add a new static widget script that, once embedded via that snippet
  on any third-party site, renders either:
  - a floating launcher bubble (position configurable via a
    `data-position` attribute) that opens into the chat panel, or
  - the chat panel mounted directly into a container element on the
    host page (no launcher, always visible), when embedded in inline
    mode

  Both modes share the same minimal, neutrally-styled chat panel
  supporting multi-turn conversation against that workspace, with a
  small "Powered by Dir Query" footer link.
- Enable permissive CORS on the existing public workspace-detail and
  ask endpoints so the widget can call them from any third-party
  origin.
- Add a `has_owner` field to workspace API responses so the frontend
  can decide whether to show the no-owner warning, without revealing
  the owner's identity.

## Capabilities

### New Capabilities
- `website-widget`: the embeddable chat widget itself, in either of
  two embed modes (a floating launcher, or an inline panel mounted
  into a host-page container), sharing one chat panel (multi-turn
  conversation, branding footer) and the cross-origin access to the
  existing workspace/ask endpoints that both modes depend on.

### Modified Capabilities
- `ask-page`: adds the "Make a widget for your website" button and its
  modal (embed-mode radio choice, snippet, copy-to-clipboard,
  conditional no-owner warning).
- `workspace-management`: adds a `has_owner` boolean to workspace
  responses, alongside the existing `can_edit` field, without
  revealing owner identity.

## Impact

- `frontend/public/w/ask/index.html`: new button, modal markup, and
  Alpine state/methods for generating and copying the snippet.
- `frontend/public/widget.js` (new file): the standalone embeddable
  widget script.
- `backend/app/schemas.py` / `backend/app/api/workspaces.py`: add
  `has_owner` to `WorkspacePublic`.
- `backend/app/main.py` (or equivalent app setup): add
  `CORSMiddleware` with `allow_origins=["*"]`,
  `allow_credentials=False`.
- No changes to conversation storage — conversations started via the
  widget are ordinary conversations, indistinguishable from ones
  started directly on the ask page.
