## Context

`backend/app/rag/index_service.py` currently hardcodes both providers:
`_get_embed_model()` always constructs a `HuggingFaceEmbedding` (local,
CPU, no API key), and `answer_question()` always constructs a MiniMax `LLM`
(`llama_index.llms.minimax.MiniMax`). The deployer's only lever today is
`MINIMAX_LLM_MODEL` / `MINIMAX_API_KEY` — everything else is a code edit.

The user has a Google AI Studio (Gemini) API key ready and wants it usable
for both roles, without losing the ability to fall back to the current
zero-cost local embedding model or to MiniMax. Verified directly by
installing and inspecting the packages (not just reading docs):
- `llama-index-llms-google-genai==0.9.6` — `GoogleGenAI(model: str =
  "gemini-3-flash-preview", api_key: str | None = None, ...)`. If `api_key`
  is not passed, it falls back to the `GOOGLE_API_KEY` env var itself, and
  if neither is set it tries OAuth/ADC rather than raising immediately.
- `llama-index-embeddings-google-genai==0.5.1` — `GoogleGenAIEmbedding(
  model_name: str = "gemini-embedding-2-preview", api_key: str | None =
  None, ...)`. Same api_key/env var/OAuth fallback behavior.

Both packages' own default models are `-preview` builds, which is not what
we want as our default (preview models can change or disappear without
notice) — this design pins its own defaults instead of relying on the
packages' built-ins.

## Goals / Non-Goals

**Goals:**
- `EMBED_PROVIDER` (`cpu` | `gemini`) and `LLM_PROVIDER` (`minimax` |
  `gemini`) are independently selectable via environment variables, each
  defaulting to today's behavior (`cpu`, `minimax`).
- A single `GOOGLE_API_KEY` credential (same file-secret/env-var pattern as
  `MINIMAX_API_KEY`) authenticates Gemini for both roles when selected.
- An invalid provider value is caught at backend startup with a clear error,
  not discovered later at request time.
- Selecting `gemini` without `GOOGLE_API_KEY` configured fails the same way
  missing `MINIMAX_API_KEY` fails today: a clear runtime error for the
  affected request/file, not a backend crash.
- Existing deployments with no new env vars set keep working identically
  (local embeddings, MiniMax completions) — this change is additive by
  default.

**Non-Goals:**
- No support for Vertex AI / OAuth-based Google auth — API-key auth only,
  matching how MiniMax is authenticated today.
- No per-workspace or per-request provider override — provider selection is
  a single deployment-wide setting, consistent with how `MINIMAX_LLM_MODEL`
  works today.
- No automatic re-embedding of already-indexed chunks if `EMBED_PROVIDER`
  changes after some documents are indexed (see Risks).
- No additional providers beyond `cpu`/`gemini` (embeddings) and
  `minimax`/`gemini` (completions) in this change.
- No UI for provider selection — environment-variable configuration only,
  consistent with `MINIMAX_LLM_MODEL` and every other deploy-time setting in
  this project.

## Decisions

### 1. Two independent enum-style env vars, not one combined "provider"
`EMBED_PROVIDER` and `LLM_PROVIDER` are separate variables rather than a
single `PROVIDER=gemini` switch, because the user explicitly wants to mix
and match (e.g. keep free local embeddings while trying Gemini for
completions, or vice versa). A combined switch would force an all-or-nothing
choice that doesn't match the stated use case.
- **Alternative considered**: one `LLM_PROVIDER=minimax|gemini` var that
  implies the embedding provider too. Rejected — loses the independence the
  user asked for, and conflates two genuinely separate concerns (indexing
  cost/latency vs. completion quality/cost).

### 2. Provider selection is validated eagerly, at import time in `config.py`
`EMBED_PROVIDER` and `LLM_PROVIDER` are read and validated against their
allowed literal sets (`{"cpu", "gemini"}`, `{"minimax", "gemini"}`) when
`app.config` is imported (backend process startup), raising `ValueError`
immediately with the bad value and the allowed set if invalid. This is a
deploy-time misconfiguration (a typo in `docker-compose.yml`/`.env`), not a
transient/runtime condition — it should fail the container fast and loudly,
the same way a missing `POSTGRES_PASSWORD` already does
(`${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}` in
`docker-compose.yml`).
- **Alternative considered**: validate lazily inside `_get_embed_model()` /
  the LLM factory, returning a clear error only when a request actually
  needs that provider. Rejected — with lazy validation, a typo'd
  `EMBED_PROVIDER` would go unnoticed through `docker compose up` and only
  surface on the *next* upload, and a typo'd `LLM_PROVIDER` only on the next
  `/ask` — both strictly worse for a deployer debugging their own config
  than an immediate startup failure. This is a different situation from the
  existing missing-`MINIMAX_API_KEY` case (Decision 4 below): a missing
  *credential* is plausible even in a correct config (the deployer hasn't
  gotten a key yet, and indexing must still work without one); an
  unrecognized *provider name* is never valid and has no such legitimate
  "not configured yet" state.

### 3. Provider dispatch lives in `index_service.py` as small factory functions, not a new abstraction layer
`_get_embed_model()` is extended with an `if EMBED_PROVIDER == "gemini": ...
else: ...` branch (constructing `GoogleGenAIEmbedding` vs. the existing
`HuggingFaceEmbedding`), and a new `_get_llm()` factory does the same for
`LLM_PROVIDER` (`GoogleGenAI` vs. the existing `MiniMax`), replacing the
inline `MiniMax(...)` construction in `answer_question()`. Both factories
are cached module-level singletons, mirroring the existing `_embed_model`
global.
- **Alternative considered**: a `Protocol`/plugin registry
  (`PROVIDERS: dict[str, Callable[[], BaseEmbedding]]`) for future
  extensibility. Rejected as premature — there are exactly two options per
  role today, an `if/else` is more readable than a registry for two
  branches, and both llama-index classes already implement the same
  `BaseEmbedding`/`LLM` interfaces the rest of `index_service.py` consumes,
  so no new abstraction is actually needed to keep the call sites
  provider-agnostic.

### 4. `GOOGLE_API_KEY` uses the existing `_read_secret` helper; missing-key behavior mirrors `MINIMAX_API_KEY` exactly
`config.py` adds `GOOGLE_API_KEY = _read_secret("GOOGLE_API_KEY")`, read from
`secrets/google_api_key.txt` (or the `GOOGLE_API_KEY` env var fallback),
identical to how `MINIMAX_API_KEY` is read today. The Gemini LLM/embedding
factories raise `RuntimeError("GOOGLE_API_KEY is not configured")` when
`LLM_PROVIDER`/`EMBED_PROVIDER` is `gemini` and the key is absent — the LLM
case is already caught by `ask.py`'s existing `except RuntimeError` handler
(503 response) with no changes needed there. The embedding case is caught by
`index_uploaded_file`'s existing broad `try/except` (logs, sets
`file.status = "failed"`), also with no changes needed.
- **Why not rely on the packages' own `GOOGLE_API_KEY` env var fallback**:
  both Gemini packages already read `GOOGLE_API_KEY` from the environment if
  `api_key` isn't passed (see Context) — but silently, and they fall through
  to OAuth/ADC instead of raising when no key is found at all, which would
  produce a confusing low-level auth error deep inside a Google SDK call
  rather than the project's existing clear "X is not configured" message.
  Explicitly checking `GOOGLE_API_KEY` ourselves before construction (same
  as the current `MINIMAX_API_KEY` check) keeps error behavior consistent
  across both providers.

### 5. `GEMINI_LLM_MODEL` defaults to `gemini-3-flash-preview`; `GEMINI_EMBED_MODEL` keeps its own default
`GEMINI_EMBED_MODEL` defaults to `gemini-embedding-001` — configurable via
env var, mirroring `MINIMAX_LLM_MODEL`. `GEMINI_LLM_MODEL` was originally
planned to default to `gemini-2.5-flash` (a stable, non-preview model,
avoiding the installed package's own `-preview` default on the reasoning
that preview models are more likely to be deprecated or change behavior
without notice) — **superseded during implementation verification**: a live
`generate_content` call against a fresh API key returned `404 NOT_FOUND
... "This model models/gemini-2.5-flash is no longer available to new
users"`. Further live probing of the same key found `gemini-2.5-flash-lite`
also 404s for new users, `gemini-2.0-flash` returns `429
RESOURCE_EXHAUSTED` (quota), and the floating `gemini-flash-latest` alias
returned a persistent `503 UNAVAILABLE` (high demand) across three retries.
Only `gemini-3-flash-preview` — the installed package's own default —
actually answered. Confirmed with the user: default to
`gemini-3-flash-preview` instead, accepting the preview-model churn risk
this decision originally tried to avoid, since it's the only option that
demonstrably works for a new deployer's key right now.
- **Risk carried forward**: like `MINIMAX_LLM_MODEL`, this default will need
  a manual update if/when Google changes what's available to new API keys
  again (evidently an active, fast-moving situation as of this
  verification) — acceptable, since it's a one-line, one-place change (same
  trade-off already accepted for `MINIMAX_LLM_MODEL`), and `AGENTS.md`
  documents how to find a currently-working replacement
  (`client.models.list()` via the `google-genai` SDK).

### 6. Embedding dimensionality is reconciled by a manual reset script, not padded to a shared size
`bge-small-en-v1.5` (local) produces 384-dimensional vectors;
`gemini-embedding-001` natively produces up to 3072 (truncatable via its
`output_dimensionality` config, but only 768/1536/3072 are dimensions Google
documents as validated — arbitrary smaller targets like 384 are not). The
`chunks.embedding` `pgvector` column has a single fixed dimension at any
point in time. Padding every vector out to a shared maximum dimension was
considered and **rejected**: two different embedding models produce vectors
in unrelated vector spaces, so cosine distance between them is meaningless
*regardless of whether their dimensions match* — padding would silently
replace today's loud, correct dimension-mismatch error with silently wrong
retrieval results, while also permanently taxing storage/compute for the
default (free, local) case to accommodate a comparison that can't be made
correct anyway.
- **Decision**: since only one `EMBED_PROVIDER` is active per deployment at
  a time (Decision 1 — never mixed within a single `chunks` table), the
  column only ever needs to match whatever the *currently* configured
  provider produces. A new operational script,
  `backend/scripts/reset_embeddings.py`, makes switching providers on an
  existing deployment a single explicit command instead of manual SQL: it
  (1) determines the target dimension by calling the currently configured
  embedding provider's factory (`index_service._get_embed_model()`) on a
  short probe string and measuring the returned vector's length — not a
  hardcoded per-provider dimension table, since the actual dimension depends
  on the specific model configured (`GEMINI_EMBED_MODEL` is itself
  configurable and could change to a model with a different native size);
  (2) `TRUNCATE`s `chunks`; (3) runs `ALTER TABLE chunks ALTER COLUMN
  embedding TYPE vector(<target_dim>)` — safe unconditionally because the
  table was just truncated, so there is no existing data to convert; (4)
  resets every `files.status` from `indexed`/`failed` back to `pending`.
  After the script runs, the existing incremental startup sync (or the next
  backend restart) re-embeds every file under the new provider automatically
  — no separate re-indexing trigger is needed.
- **The script is a manual, explicit step — not run automatically on every
  provider change.** Provider switching on a live deployment with existing
  data is expected to be rare (mostly a fresh-deploy decision), and running
  a destructive `TRUNCATE`/`ALTER` automatically whenever `EMBED_PROVIDER`
  differs from some stored value is riskier than requiring a deliberate
  command. This mirrors the general project pattern (e.g. Alembic migrations
  are also a manual, explicit step, never auto-applied on startup).
- **`Chunk.embedding`'s Python-level `Vector(EMBEDDING_DIM)` type stays as
  the initial-migration default only.** The ORM column type is not re-read
  or re-validated at runtime against the live database column — pgvector's
  SQLAlchemy `Vector` type is a serialization helper (Python list ↔
  Postgres `vector` literal), and dimension is actually enforced by
  Postgres's column typmod, which the reset script owns going forward. This
  should be verified empirically during implementation (inspecting the
  installed `pgvector-sqlalchemy` package, matching how the previous change
  verified `MiniMax`'s constructor before relying on it) rather than
  assumed.
- **Alternative considered**: force Gemini to truncate to exactly 384 via
  `output_dimensionality`, so the column's dimension never changes and no
  `ALTER TABLE` is ever needed. Rejected — 384 is below the dimensions
  Google documents as validated for `gemini-embedding-001` (768/1536/3072),
  so retrieval quality at that size is unverified; resizing the column to a
  provider's real, validated output is more correct at the cost of the
  `ALTER TABLE` step, which the reset script already has to include for
  other reasons (see below).
- **Alternative considered**: an automated migration/guard that detects a
  provider/dimension mismatch and rebuilds transparently. Rejected — same
  reasoning as before: an automatic destructive operation triggered by a
  config change is a worse failure mode than a deployer running one
  documented, explicit script.

## Risks / Trade-offs

- **[Risk]** Switching `EMBED_PROVIDER` after documents are already indexed
  breaks retrieval (dimension mismatch or, even if dimensions coincidentally
  matched, incomparable vector spaces) unless the deployer remembers to run
  `reset_embeddings.py`. → **Mitigation**: the script is documented in
  `AGENTS.md` as a required step when changing `EMBED_PROVIDER` on an
  existing deployment (Decision 6); if forgotten, the pre-existing
  `pgvector` dimension-mismatch error still fails loudly at query/insert
  time rather than silently returning wrong results, so the failure mode is
  a clear error either way, not silent corruption.
- **[Risk]** `reset_embeddings.py` is destructive (`TRUNCATE chunks`) and
  has no built-in confirmation prompt or dry-run mode. → **Mitigation**:
  accepted for an operator-run script at this project's beta scale
  (consistent with there being no undo for other manual operational steps
  in this project, e.g. deleting `secrets/*.txt`); documented clearly in
  `AGENTS.md` as a destructive, deliberate action. A confirmation
  prompt/`--yes` flag can be added later if this proves error-prone in
  practice.
- **[Risk]** Gemini's free tier (1,500 requests/day cited by the user) is a
  hard cap; a deployer who selects `gemini` for indexing on a large document
  set could hit it mid-sync, leaving some files `failed`. → **Mitigation**:
  existing per-file failure handling (log + `status = failed`) already
  covers this — a failed file is retried on the next startup sync per the
  existing `document-indexing` behavior, no new mechanism needed.
- **[Risk]** The Gemini packages' silent OAuth/ADC fallback (Context) means
  a future contributor who removes our explicit key check could
  reintroduce confusing errors instead of the project's clear
  "not configured" message. → **Mitigation**: covered by a unit test
  asserting the `RuntimeError` is raised before any Gemini SDK call is
  attempted when `GOOGLE_API_KEY` is unset and `LLM_PROVIDER`/
  `EMBED_PROVIDER` is `gemini`.
- **[Risk]** Google's data-use terms (prompts used to improve models, except
  in EU/UK/EEA — cited by the user as the reason it's acceptable for a
  Netherlands-based deployment) are a business/legal judgment, not something
  this change can verify or enforce in code. → **Mitigation**: none needed
  in code; noted here only because it's part of the user's stated reasoning
  for wanting this provider option available.

## Migration Plan

No schema migration ships with this change (the reset script's `ALTER
TABLE` in Decision 6 runs on-demand, only when a deployer actually switches
providers — not as part of rollout). Rollout is additive: existing
deployments with no new env vars set (`EMBED_PROVIDER`/`LLM_PROVIDER` both
unset) are unaffected — `_get_embed_model()`/`_get_llm()` default to today's
exact behavior. To opt into Gemini: set `LLM_PROVIDER=gemini` and/or
`EMBED_PROVIDER=gemini` in `.env`/`docker-compose.yml`, and supply
`GOOGLE_API_KEY` via `secrets/google_api_key.txt` (recommended, copied from
a new `secrets/google_api_key.txt.example`) or the plain `GOOGLE_API_KEY`
env var fallback — same mechanism as `MINIMAX_API_KEY` today. If switching
`EMBED_PROVIDER` on a deployment with existing indexed chunks, the deployer
must run `backend/scripts/reset_embeddings.py` (Decision 6) before the new
provider's embeddings are usable — this clears `chunks`, resizes the
`embedding` column to the new provider's dimension, and resets `files`
back to `pending` so the next startup sync re-indexes everything under the
new provider. Rollback is reverting the env vars (and, if `EMBED_PROVIDER`
was changed and the reset script already ran, running it again after
reverting, since the column dimension must match whichever provider is
actually configured).

## Open Questions

- Should `GEMINI_LLM_MODEL/GEMINI_EMBED_MODEL` defaults be re-pinned once
  Gemini 3 models stabilize out of preview? Deferred to a future change,
  same as any other model-default update.

**Resolved**: No startup warning when `EMBED_PROVIDER` differs from the
provider implied by existing chunks (e.g. via a `provider` column on
`chunks`) — that would need a schema change disproportionate to this
change's scope. Documenting the requirement to run `reset_embeddings.py`
after changing `EMBED_PROVIDER` in `AGENTS.md` is sufficient; the existing
`pgvector` dimension-mismatch error remains the runtime backstop if a
deployer forgets (see Risks).
