## Why

The embedding model (local HuggingFace) and the completion model (MiniMax) are
each hardcoded to a single provider in `backend/app/rag/index_service.py`. A
deployer who wants to run without a GPU-hungry local embedding model, who
doesn't have a MiniMax key, or who already has a Google AI Studio (Gemini)
key ready to use, currently has no way to switch — the only way to change
provider is to edit application code. This change introduces an
environment-variable-driven provider selection for both the embedding model
and the completion (LLM) model, and adds Gemini as the first alternative
provider for both, alongside the existing local-embedding/MiniMax defaults.

## What Changes

- Add an `EMBED_PROVIDER` environment variable selecting the embedding
  provider: `cpu` (the current local HuggingFace `bge-small-en-v1.5` model —
  default, preserves existing behavior) or `gemini` (Google's Gemini
  embeddings API).
- Add an `LLM_PROVIDER` environment variable selecting the completion
  provider: `minimax` (current default, preserves existing behavior) or
  `gemini` (Google's Gemini chat API).
- The two selections are independent — a deployer can, for example, run local
  embeddings with a Gemini LLM, or Gemini embeddings with a MiniMax LLM.
- Add Gemini support via `llama-index-llms-google-genai` and
  `llama-index-embeddings-google-genai`, authenticated with a `GOOGLE_API_KEY`
  credential, read the same way `MINIMAX_API_KEY` is today (file-based Docker
  secret, recommended, with a plain env var fallback).
- Add `GEMINI_LLM_MODEL` and `GEMINI_EMBED_MODEL` environment variables
  (each with a sensible default) mirroring the existing `MINIMAX_LLM_MODEL`
  pattern, so the specific Gemini model is configurable without a code change.
- An unrecognized `EMBED_PROVIDER` or `LLM_PROVIDER` value fails backend
  startup with a clear error (a deploy-time misconfiguration), rather than
  silently falling back to a default.
- Selecting `gemini` for either provider without a configured `GOOGLE_API_KEY`
  behaves like the existing missing-`MINIMAX_API_KEY` case: indexing/`/ask`
  fail clearly for that request/file without crashing the backend process.
- Add a manual `backend/scripts/reset_embeddings.py` script for switching
  `EMBED_PROVIDER` on a deployment that already has indexed chunks: it
  clears the `chunks` table, resizes the `pgvector` `embedding` column to
  match the newly configured provider's actual output dimension, and resets
  affected files back to `pending` so the existing incremental startup sync
  re-indexes everything under the new provider. Different embedding
  providers produce vectors in incompatible vector spaces (not just
  different dimensions), so this reset is required — there is no way to
  keep old and new embeddings side by side in the same column.
- **BREAKING**: the `document-indexing` capability's "requires no external API
  credentials" requirement no longer holds unconditionally — it now holds
  only for the default `EMBED_PROVIDER=cpu`. Deployers who opt into
  `EMBED_PROVIDER=gemini` must supply `GOOGLE_API_KEY` for indexing to work.

## Capabilities

### New Capabilities
- `llm-provider-selection`: deployer-facing capability that lets the
  embedding provider and the completion (LLM) provider each be chosen
  independently via environment variables, validated at backend startup,
  with Gemini and the existing defaults (local embeddings, MiniMax) as the
  available options.

### Modified Capabilities
- `document-indexing`: the "Indexing uses a local embedding model, requiring
  no external API credentials" requirement is replaced — indexing now uses
  whichever embedding provider is configured via `EMBED_PROVIDER`, which is
  local/no-credential only when left at its default.
- `question-answering`: the "Question-answering uses MiniMax for completions"
  requirement is replaced — question-answering now uses whichever LLM
  provider is configured via `LLM_PROVIDER`, which is MiniMax only when left
  at its default.

## Impact

- `backend/app/config.py`: new `EMBED_PROVIDER`, `LLM_PROVIDER`,
  `GEMINI_LLM_MODEL`, `GEMINI_EMBED_MODEL` env vars; new `GOOGLE_API_KEY`
  secret read via the existing `_read_secret` helper; startup validation of
  the two provider selections.
- `backend/app/rag/index_service.py`: `_get_embed_model()` and the LLM
  construction in `answer_question()` become provider-dispatching instead of
  hardcoded.
- `backend/pyproject.toml`: new dependencies `llama-index-llms-google-genai`
  and `llama-index-embeddings-google-genai`.
- `docker-compose.yml` / `.env.example`: new `EMBED_PROVIDER`, `LLM_PROVIDER`,
  `GEMINI_LLM_MODEL`, `GEMINI_EMBED_MODEL` env vars; `GOOGLE_API_KEY` wired
  the same way `MINIMAX_API_KEY` is (bind-mounted `secrets/` directory).
- `secrets/`: new `google_api_key.txt.example` placeholder, gitignored real
  file like `minimax_api_key.txt`.
- `backend/scripts/reset_embeddings.py`: new operational script (see What
  Changes) for switching `EMBED_PROVIDER` on a deployment with existing
  indexed data; runs a `TRUNCATE` and an `ALTER TABLE ... ALTER COLUMN
  embedding TYPE vector(N)` against `chunks`.
- `AGENTS.md`: documents the new env vars, how to supply a Gemini key, and
  how/when to run `reset_embeddings.py`.
- No changes to `document-upload`, `ask-page`, `home-page`, or
  `workspace-management`.
