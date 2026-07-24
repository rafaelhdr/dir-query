## Context

Workspaces today are write-once outside of their content: `POST /workspaces`
creates one (name, slug, description, `key_source`/`key_provider`/encrypted
credential, optional owner), and `GET /workspaces` / `GET /workspaces/{slug}`
read them back. Editing existing content (files) already has a permission
model — `_can_edit` in `backend/app/api/workspaces.py:16-19` — reused
verbatim by document-upload and document-management. This change extends
that same model to the workspace's own fields for the first time, and
explicitly reverses workspace-llm-key-selection's "fixed at creation"
requirement.

## Goals / Non-Goals

**Goals:**
- Let an editor change a workspace's name, description, and LLM key
  configuration after creation, reusing the existing `can_edit` permission
  computation unchanged.
- Keep the slug in sync with the name, with predictable, non-silent
  collision handling.
- Support switching `key_source` freely in both directions without leaving
  orphaned encrypted credentials behind.

**Non-Goals:**
- No slug history/redirects for old URLs — out of scope, explicitly
  decided against.
- No true partial-PATCH semantics — the endpoint always takes the full
  field set.
- No changes to `_can_edit`'s logic, to embedding provider selection, or to
  document-management (file rename is untouched).
- No embeddable widget — a future capability that will let people embed a
  workspace on their own website is planned but not built here. Because
  no redirect/alias is kept for an old slug (see above), a rename would
  silently break such an embed once it exists, the same way it breaks a
  link in a blog post today. The rename warning added by this change is
  worded generically enough to cover that future case without depending
  on the widget existing yet.

## Decisions

**Slug recomputation on rename, reject on collision.** Reuses the same
`slugify()` used at creation (`backend/app/services/slug.py`) and the same
conflict-rejection pattern as `create_workspace`'s `IntegrityError` handler
(`workspaces.py:93-100) — a unique constraint on `slug` already exists, so
the update can rely on the same DB-level uniqueness check rather than a
separate pre-check, collapsing the `IntegrityError` into the same 409
response shape as creation.

**No slug aliasing.** Considered keeping a redirect table from old → new
slug, but that adds a new table and a lookup on every 404, for a workspace
count and edit frequency where broken bookmarks are an acceptable,
already-agreed-to cost. Simpler wins.

**Full-submission PATCH, not partial.** The settings page is a single form
with one Save action, so there's no UI case that needs to send a subset of
fields. Full submission means the same required-field validation as
`create_workspace` can be reused almost as-is (name non-empty, dedicated
requires provider) instead of writing a second "what's present vs. absent"
branch.

**Credential required only on provider change / entry into dedicated.**
Because the API never returns a stored credential (workspace-llm-key-
selection's existing "never returned" requirement, unchanged), the
settings form cannot prefill it. Blank must mean "unchanged" when nothing
about the provider is changing, or every edit that merely fixes a typo in
the description would force the owner to go dig up their API key again.
The distinguishing signal is `key_provider` changing, or `key_source`
transitioning into `dedicated` from something else — both computable
server-side by comparing the request against the current row before
touching it.

**Discard credential immediately on dedicated → system.** Considered
keeping it "inactive" for a instant switch-back, but that requires a new
status column and leaves a live encrypted secret sitting unused
indefinitely for a scenario (switch back to the exact same dedicated key)
that's easy enough to redo by re-entering it. Discarding matches the
spirit of "never returned, minimal retention" already established for
these credentials.

**Settings as a new page, not inline on the content page.** The LLM key
form is already substantial on `/workspaces/new` (source, provider,
credential fields); embedding it inline in the content-page header would
compete for space with the file list. A dedicated page mirrors the
existing Ask/Content page-per-concern split.

## Risks / Trade-offs

- **[Breaking change to workspace-llm-key-selection]** → Documented
  explicitly in the proposal as **BREAKING** and reflected as a MODIFIED
  requirement in that capability's delta spec, not silently dropped.
- **[Old slug URLs 404 after a rename]** → Accepted trade-off; the frontend
  navigates to the new URL immediately after a successful rename so the
  user doing the editing never hits it themselves.
- **[Discarding a dedicated credential on switch-to-system is irreversible]**
  → The credential was never visible to the owner after entry anyway (API
  never returns it), so this doesn't reduce anything the owner could
  previously recover; they re-enter it if they switch back.
- **[Slug collision uses a DB constraint rather than a pre-check]** → Same
  approach `create_workspace` already uses; consistent behavior, no new
  race-condition surface introduced.

## Migration Plan

No data migration needed — no schema change (existing columns already
support arbitrary `key_source`/`key_provider`/`encrypted_api_key` values).
Deploy the new endpoint and page together; no rollback complexity beyond
reverting the deploy, since old rows are unaffected by the capability
existing.

## Open Questions

None outstanding — all decisions above were confirmed during the grilling
session that produced this change.
