## Context

Today, `LLM_PROVIDER`/`EMBED_PROVIDER` and their credentials
(`MINIMAX_API_KEY`, `GOOGLE_API_KEY`) are deployment-wide environment
configuration (`app/config.py`), resolved once at process start and used by
every workspace via `app/rag/index_service.py`'s `_get_llm()`. Workspace
creation (`POST /api/workspaces`, `app/api/workspaces.py`) only accepts a
`name`. There is no workspace edit endpoint or page. `Exchange` rows
(`app/db/models.py`) record `question`/`answer`/`sources`/`status` but
nothing about which LLM answered them.

This change adds a per-workspace override: a workspace can either keep
using the system's shared key (default, matches today) or supply its own
Gemini or MiniMax key at creation time, stored encrypted, used only for that
workspace's `/ask` calls.

## Goals / Non-Goals

**Goals:**
- Let a workspace owner opt into their own Gemini/MiniMax key at creation
  time, so their questions aren't subject to the shared system key's limits.
- Never persist a dedicated key in plaintext.
- Record, per answered exchange, whether the system or a dedicated key
  answered it, and which provider — for transparency/debugging, not for
  billing enforcement.
- Keep the change additive to `question-answering`: when a workspace has no
  dedicated key, behavior is byte-for-byte what it is today.

**Non-Goals:**
- Editing a workspace's key configuration after creation (no PATCH
  endpoint/page in this change).
- Applying dedicated keys to embedding/indexing — `EMBED_PROVIDER` stays
  global.
- Verifying a dedicated key works (e.g. a live test call) at creation time.
- Enforcing usage/billing limits against a dedicated key — the provider's
  own account billing is the enforcement mechanism.

## Decisions

### Storage shape: typed columns on `workspaces`, not a JSON blob
Add `description` (`text`, not null, default `""`), `key_source`
(`text`, not null, default `'system'`, `CheckConstraint` `IN ('system',
'dedicated')`), `key_provider` (`text`, nullable, `CheckConstraint` `IN
('gemini', 'minimax')` when not null), `encrypted_api_key` (`text`,
nullable). This mirrors the existing `FILE_STATUSES`/`EXCHANGE_STATUSES`
CheckConstraint convention in `app/db/models.py`, giving DB-level
enforcement of the allowed value sets, at the cost of a migration if the
shape changes later (acceptable — this mirrors how every other typed field
in this schema is modeled).

### Encryption: Fernet keyed off a new dedicated secret
Use `cryptography`'s `Fernet` symmetric encryption (new dependency in
`backend/pyproject.toml`). The Fernet key is derived from a new secret,
`WORKSPACE_KEY_ENCRYPTION_SECRET`, resolved via the same `_read_secret()`
helper in `app/config.py` used for `JWT_SECRET_KEY`/`MINIMAX_API_KEY`
(secrets-file preferred, `.env` fallback), with a matching
`secrets/workspace_key_encryption_secret.txt.example`. Since an arbitrary
operator-chosen secret string won't generally be a valid 32-byte
url-safe-base64 Fernet key, derive one deterministically:
`base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())`.

This secret is deliberately independent from `JWT_SECRET_KEY` — rotating
the JWT signing secret (e.g. to invalidate all sessions after an incident)
must not also silently corrupt every stored dedicated API key, and vice
versa. Missing `WORKSPACE_KEY_ENCRYPTION_SECRET` at workspace-creation time
with `key_source=dedicated` fails that request with a clear 503-style
configuration error, following the existing pattern for missing
`JWT_SECRET_KEY`/provider credentials — it does not crash the backend.

### `/ask` provider resolution: workspace override, else global config
`app/rag/index_service._get_llm()` currently reads `LLM_PROVIDER`,
`GOOGLE_API_KEY`, `MINIMAX_API_KEY` from `app/config.py` unconditionally.
It changes to accept the calling workspace's `key_source`/`key_provider`/
decrypted credential: when `key_source == "dedicated"`, build the
Gemini/MiniMax client using the workspace's own provider and decrypted key
(same `GEMINI_LLM_MODEL`/`MINIMAX_LLM_MODEL` model names as today — only the
credential and provider selection are overridden); when `key_source ==
"system"`, behavior is unchanged (today's global-config path). Decryption
happens in-process, per request, right before constructing the LLM client —
the decrypted key is never logged or persisted anywhere beyond that local
variable.

### Exchange snapshot, not a live join
`app/services/conversations.ask()` reads the workspace's `key_source`/
`key_provider` at the moment it calls `index_service.answer_question(...)`
and writes `llm_key_source`/`llm_provider` onto the `Exchange` row when
marking it `answered`. This is a factual record of what answered that
specific exchange, independent of whatever the workspace's config might
become in a future change that adds editing. Existing `Exchange` rows get
`NULL` for both new columns (unknown, not retroactively inferable).

### API exposure: owner-only for key config, public for description
`WorkspacePublic` gains `description: str` (always present, empty string if
none — consistent with the non-nullable column) visible to everyone,
matching how `description` is meant to appear under every workspace's title
on the public `/workspaces` list. `key_source`/`key_provider` are only
populated when `can_edit=True` for the requester (`None` otherwise) — same
per-request `can_edit` computation `app/api/workspaces.py` already does for
ownership, just gating two more fields instead of a boolean. The encrypted
key itself is never added to any Pydantic response model.

### Frontend: single credential field, label swaps with provider radio
`/workspaces/new` gets an `<details>` "Advanced" block containing the
System/Dedicated radio (with the free-but-limited / charged-to-your-account
copy) and, only when Dedicated is checked, a second Gemini/MiniMax radio
plus one `type="password"` credential input. A small inline script toggles
visibility and the input's label/placeholder text based on the selected
provider, mirroring the existing vanilla-JS pattern already used on this
page for handling the `htmx:afterRequest` response.

### Validation: reject empty credential server-side, no live key test
`POST /api/workspaces` rejects the request with 400 if `key_source=dedicated`
and either `key_provider` or the credential is missing/blank — same
validation style as the existing "name must contain at least one letter or
number" check. No outbound call is made to Gemini/MiniMax to verify the key
works; a bad key simply fails later at ask-time through the existing
generic-502 exception handling in `app/api/ask.py`, unchanged.

## Risks / Trade-offs

- **[Risk]** A bad/typo'd dedicated key isn't caught until the first
  question is asked, which may be confusing (workspace "looks" created
  successfully). → **Mitigation**: explicitly deferred per this change's
  scope (see Non-Goals); acceptable because the failure mode matches
  today's system-key failure UX (generic 502), not a new failure class.
- **[Risk]** Losing/rotating `WORKSPACE_KEY_ENCRYPTION_SECRET` makes every
  previously stored dedicated key permanently undecryptable. → **Mitigation**:
  documented in `AGENTS.md` alongside the other secrets, same operational
  caveat as losing `JWT_SECRET_KEY` (which invalidates all sessions);
  no automatic re-encryption/rotation tooling is in scope for this change.
- **[Risk]** No creation-time key edit means a workspace owner who mistypes
  their key must create a new workspace to fix it. → **Mitigation**:
  acceptable for this change's explicit no-edit scope; noted as a natural
  follow-up.

## Migration Plan

Single additive Alembic migration:
- `workspaces`: add `description` (`NOT NULL DEFAULT ''`), `key_source`
  (`NOT NULL DEFAULT 'system'`), `key_provider` (nullable), `encrypted_api_key`
  (nullable), plus the two `CheckConstraint`s.
- `exchanges`: add `llm_key_source`, `llm_provider` (both nullable, no
  default — existing rows stay `NULL`).

All new columns are additive with safe defaults/nullability, so this is a
standard zero-downtime migration; no backfill script needed. Rollback is a
straight `alembic downgrade` dropping the new columns.

## Open Questions

None outstanding — scope, storage, encryption, and exposure were confirmed
during the grilling session preceding this proposal.
