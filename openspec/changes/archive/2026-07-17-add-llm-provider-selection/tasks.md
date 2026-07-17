## 1. Dependencies

- [x] 1.1 Add `llama-index-llms-google-genai` and
      `llama-index-embeddings-google-genai` to `backend/pyproject.toml`; run
      `uv sync` and confirm both install cleanly alongside the existing
      `torch`/CPU-pinned dependencies

## 2. Configuration and startup validation

- [x] 2.1 In `backend/app/config.py`, add `EMBED_PROVIDER` (default `"cpu"`)
      and `LLM_PROVIDER` (default `"minimax"`) read from their respective
      env vars
- [x] 2.2 Validate `EMBED_PROVIDER` against `{"cpu", "gemini"}` and
      `LLM_PROVIDER` against `{"minimax", "gemini"}` at module import time,
      raising `ValueError` naming the invalid variable, its value, and the
      allowed values if either is unrecognized
- [x] 2.3 Add `GEMINI_LLM_MODEL` (default `"gemini-3-flash-preview"` — revised
      during verification, see task 8.3 and design.md Decision 5: live
      testing found `gemini-2.5-flash` 404s for new API keys) and
      `GEMINI_EMBED_MODEL` (default `"gemini-embedding-001"`) env vars
- [x] 2.4 Add `GOOGLE_API_KEY = _read_secret("GOOGLE_API_KEY")`, using the
      existing `_read_secret` helper (same pattern as `MINIMAX_API_KEY`)
- [x] 2.5 Add tests in `backend/tests/test_config.py` covering: default
      provider values when unset, a valid non-default value for each
      variable, and a `ValueError` for an invalid value for each variable

## 3. Embedding provider dispatch

- [x] 3.1 In `backend/app/rag/index_service.py`, extend `_get_embed_model()`
      to branch on `EMBED_PROVIDER`: `"cpu"` keeps the existing
      `HuggingFaceEmbedding` construction; `"gemini"` constructs
      `GoogleGenAIEmbedding(model_name=GEMINI_EMBED_MODEL,
      api_key=GOOGLE_API_KEY)`, raising `RuntimeError("GOOGLE_API_KEY is not
      configured")` first if `GOOGLE_API_KEY` is falsy (mirroring the
      existing `MINIMAX_API_KEY` check in `answer_question`) — checked
      before constructing the client, not relying on the package's own
      env-var/OAuth fallback
- [x] 3.2 Confirm the existing `try/except` in `index_uploaded_file` (logs
      and sets `file.status = "failed"`) already covers a `RuntimeError`
      raised from `_get_embed_model()` — no changes needed there, but add a
      test asserting a file fails cleanly (status `failed`, no crash) when
      `EMBED_PROVIDER=gemini` and `GOOGLE_API_KEY` is unset

## 4. LLM provider dispatch

- [x] 4.1 In `backend/app/rag/index_service.py`, add a `_get_llm()` factory:
      `"minimax"` (default) constructs `MiniMax(model=MINIMAX_LLM_MODEL,
      api_key=MINIMAX_API_KEY)` exactly as `answer_question` does today,
      raising `RuntimeError("MINIMAX_API_KEY is not configured")` if absent;
      `"gemini"` constructs `GoogleGenAI(model=GEMINI_LLM_MODEL,
      api_key=GOOGLE_API_KEY)`, raising `RuntimeError("GOOGLE_API_KEY is not
      configured")` if absent
- [x] 4.2 Update `answer_question()` to call `_get_llm()` instead of
      constructing `MiniMax` inline, and to call it *before* running
      retrieval (so a missing-credential error surfaces without an
      unnecessary embedding/DB round trip first) — matching the existing
      early `MINIMAX_API_KEY` check's intent, now generalized to whichever
      provider is configured
- [x] 4.3 Update `backend/tests/test_index_service.py`: adapt the existing
      MiniMax-path tests to go through `_get_llm()` (monkeypatching
      `index_service.MiniMax` as today, with `LLM_PROVIDER` left at its
      default), and add tests for: `LLM_PROVIDER=gemini` answering via a
      stubbed `GoogleGenAI`, and `LLM_PROVIDER=gemini` with no
      `GOOGLE_API_KEY` raising `RuntimeError` mentioning `GOOGLE_API_KEY`

## 5. Embedding reset script

- [x] 5.1 Create `backend/scripts/reset_embeddings.py`: determine the target
      dimension by calling `index_service._get_embed_model()` and embedding
      a short probe string, measuring the resulting vector's length (do not
      hardcode a per-provider dimension table — the real dimension depends
      on whichever specific model is currently configured)
- [x] 5.2 In the same script, against the configured `DATABASE_URL`: `TRUNCATE
      chunks`, then `ALTER TABLE chunks ALTER COLUMN embedding TYPE
      vector(<target_dim>)`, then `UPDATE files SET status = 'pending'
      WHERE status IN ('indexed', 'failed')` — run as one transaction
- [x] 5.3 Verify empirically (inspecting the installed `pgvector-sqlalchemy`
      package, per design.md Decision 6) that the ORM's static
      `Chunk.embedding` `Vector(EMBEDDING_DIM)` type does not need to change
      for reads/writes to keep working once the live column's dimension has
      been altered by the script; adjust the model/column type if that
      assumption doesn't hold — confirmed: `Vector`'s bind/result processors
      only serialize Python lists to/from the Postgres `vector` literal and
      never check `self.dim`, so the ORM type hint is DDL-only and the
      script owns the live column's actual dimension
- [x] 5.4 Add a test for the script (against a test database) that: seeds a
      chunk, runs the reset with a stubbed embedding provider returning a
      different-length vector, and asserts the column's new dimension,
      empty `chunks` table, and `files.status` reset to `pending`
- [x] 5.5 Document `reset_embeddings.py` in `AGENTS.md`: when to run it
      (after changing `EMBED_PROVIDER` on a deployment with existing
      indexed data), how to run it (e.g. `docker compose exec backend uv
      run python scripts/reset_embeddings.py`), and that it is destructive
      (clears all chunks) with no confirmation prompt

## 6. Docker Compose and secrets

- [x] 6.1 Add `EMBED_PROVIDER`, `LLM_PROVIDER`, `GEMINI_LLM_MODEL`,
      `GEMINI_EMBED_MODEL`, and `GOOGLE_API_KEY` (sourced from `.env`,
      defaulting to empty) as `backend` service environment variables in
      `docker-compose.yml` (also added a `./backend/scripts:/app/scripts`
      bind mount and a matching `Dockerfile` `COPY scripts ./scripts`, so
      `reset_embeddings.py` is actually present/editable in the container —
      not explicitly listed originally but required for the script to run)
- [x] 6.2 Create `secrets/google_api_key.txt.example` (placeholder content,
      e.g. `your-google-api-key-here`) — `secrets/*` except `.gitkeep` and
      `*.example` is already gitignored, so no `.gitignore` change is needed
- [x] 6.3 Add commented-out `EMBED_PROVIDER=`, `LLM_PROVIDER=`,
      `GEMINI_LLM_MODEL=`, `GEMINI_EMBED_MODEL=`, and `GOOGLE_API_KEY=`
      lines to `.env.example`, documenting the allowed values and defaults

## 7. Documentation

- [x] 7.1 Update `AGENTS.md`'s credentials section to document
      `EMBED_PROVIDER`/`LLM_PROVIDER` and how to supply `GOOGLE_API_KEY`
      (secrets file recommended, env var fallback), alongside the existing
      MiniMax instructions, and document `reset_embeddings.py` (task 5.5
      covers the actual content; this task is about linking it in from the
      main credentials/setup section)

## 8. Verification

- [x] 8.1 `uv run pytest -v` — confirm all backend tests pass, including
      the new provider-selection and reset-script tests — 42/42 passed
- [x] 8.2 With no env vars changed (all defaults), `docker compose up
      --build`; upload a PDF and ask a question; confirm behavior is
      unchanged from before this change (local embeddings, MiniMax answer)
      — confirmed live: uploaded a PDF, indexed locally (3 chunks), and
      `/ask` returned a correct MiniMax-generated answer with sources
- [x] 8.3 Set `EMBED_PROVIDER=gemini` and `LLM_PROVIDER=gemini` with a real
      `GOOGLE_API_KEY` in `secrets/google_api_key.txt`; restart; upload a
      PDF and confirm it indexes successfully; ask a question and confirm
      an answer is returned — both via the Gemini API — confirmed live: a
      PDF indexed under `gemini-embedding-001` (column resized to
      `vector(3072)` by the reset script) and `/ask` returned a correct
      answer via `gemini-3-flash-preview`. Along the way, this surfaced two
      real bugs fixed during verification: (1) `gemini-2.5-flash` (the
      originally planned `GEMINI_LLM_MODEL` default) 404s for new API keys
      — see design.md Decision 5 for the live model probing that led to
      `gemini-3-flash-preview`; (2) `Chunk.embedding`'s ORM-level
      `Vector(EMBEDDING_DIM)` type baked a hardcoded `::VECTOR(384)` cast
      into generated INSERT SQL, breaking inserts after the reset script
      resized the live column — fixed by dropping the fixed dimension at
      the ORM level (`Vector()`), see `backend/app/db/models.py`
- [x] 8.4 Set `EMBED_PROVIDER=cpu` and `LLM_PROVIDER=gemini` (mixed
      providers) and confirm indexing still succeeds locally while `/ask`
      answers via Gemini — confirmed live: after switching back to
      `EMBED_PROVIDER=cpu` and running `reset_embeddings.py` (column
      resized `vector(3072)` → `vector(384)`), the startup sync re-indexed
      both existing files locally and `/ask` (still `LLM_PROVIDER=gemini`)
      answered correctly
- [x] 8.5 Set `LLM_PROVIDER=gemini` with no `GOOGLE_API_KEY` configured;
      confirm `/ask` returns a clear configuration error (not a crash),
      matching the existing missing-`MINIMAX_API_KEY` behavior — confirmed
      live: `503` with `"Question-answering is not configured:
      GOOGLE_API_KEY is not configured"`, backend kept running
- [x] 8.6 Set `EMBED_PROVIDER=nonsense` (or `LLM_PROVIDER=nonsense`) and
      confirm `docker compose up` fails fast with a clear error naming the
      bad value, rather than starting successfully — confirmed live:
      container exits immediately with `ValueError: EMBED_PROVIDER='nonsense'
      is not a valid choice; expected one of ['cpu', 'gemini']`
- [x] 8.7 Starting from the state left by 8.3 (indexed content under
      `EMBED_PROVIDER=gemini`), switch back to `EMBED_PROVIDER=cpu`, run
      `reset_embeddings.py`, restart, and confirm: `chunks` was cleared and
      the column's dimension changed back to the local model's 384, files
      went back to `pending`, and the startup sync re-indexed them under
      the local provider so `/ask` works again without a dimension error
      — confirmed live (this run doubled as the 8.4 mixed-provider check):
      column went `vector(3072)` → `vector(384)`, both files went back to
      `pending` and were re-indexed locally on restart, and `/ask` (still
      `LLM_PROVIDER=gemini`) answered correctly afterward.
      `reset_embeddings.py` was additionally exercised directly by an
      automated test and by earlier manual runs against the live dev
      database (`vector(384)` → `vector(768)` → back to `vector(384)`) —
      see task 5.
