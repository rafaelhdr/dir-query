## Why

Answering questions today always uses the backend's shared system LLM
credential (`LLM_PROVIDER`/`MINIMAX_API_KEY`/`GOOGLE_API_KEY`), which is free
to use but limited and can fail under load or quota pressure. Workspace
owners who want reliable answers, or who want a specific provider, need a
way to bring their own API key, scoped to their workspace, without touching
deployment-level `.env` configuration. Workspaces also currently have no way
to describe themselves beyond a name, making the all-workspaces list hard to
navigate once there are more than a few.

## What Changes

- Add an optional `description` field to workspace creation, shown on the
  all-workspaces list page below each workspace's title, rendered as
  sanitized Markdown with line breaks (reusing the ask page's
  `marked`/`DOMPurify` rendering).
- Add a per-workspace LLM key choice at creation time, presented in a
  collapsed "Advanced" section on the `/workspaces/new` form:
  - **System API Keys** (default) — uses the backend's existing shared
    credentials, same as today.
  - **Dedicated** — the workspace owner supplies their own API key for
    either Gemini or MiniMax, charged to their own account.
- Store the dedicated credential encrypted at rest (never in plaintext),
  using a new dedicated encryption secret independent of `JWT_SECRET_KEY`.
- Store only the *type* of key used (`system`/`dedicated`) and, when
  dedicated, the provider (`gemini`/`minimax`) — never the raw key — on the
  workspace, and expose these to the workspace owner only.
- `/w/<slug>/ask` uses the workspace's dedicated key/provider when
  configured, falling back to the system-wide `LLM_PROVIDER` credential
  otherwise; each answered exchange records a snapshot of which key source
  and provider actually answered it.
- Scoped to question-answering only — embedding/indexing continues to use
  the global `EMBED_PROVIDER` regardless of a workspace's key configuration.
- No editing after creation in this change — workspace key configuration is
  set once, at creation time.

## Capabilities

### New Capabilities
- `workspace-llm-key-selection`: Per-workspace choice between the system's
  shared LLM credentials and a dedicated, owner-supplied API key (Gemini or
  MiniMax), captured at workspace creation, encrypted at rest, and exposed
  only to the workspace owner.

### Modified Capabilities
- `workspace-management`: Workspace creation gains an optional `description`
  field (shown on the workspace list); workspace API responses gain
  `description` (public) and owner-only `key_source`/`key_provider` fields.
- `question-answering`: `/ask` uses a workspace's dedicated key/provider when
  configured instead of the global `LLM_PROVIDER`, and each exchange records
  which key source and provider actually generated its answer.

## Impact

- **DB**: new columns on `workspaces` (`description`, `key_source`,
  `key_provider`, `encrypted_api_key`) and on `exchanges` (`llm_key_source`,
  `llm_provider`); new Alembic migration.
- **Backend**: `app/db/models.py`, `app/schemas.py`,
  `app/api/workspaces.py`, `app/rag/index_service.py`,
  `app/services/conversations.py`, `app/config.py` (new
  `WORKSPACE_KEY_ENCRYPTION_SECRET`), new `secrets/*.example` file, new
  encryption helper module; new `cryptography` dependency.
- **Frontend**: `frontend/public/workspaces/new/index.html` (description
  textarea + Advanced key section), `frontend/public/workspaces/index.html`
  (render description).
- No changes to `llm-provider-selection` (system-wide default provider
  selection is unchanged) or to embedding/indexing behavior.
