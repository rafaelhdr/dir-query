## 1. Dependencies and configuration

- [x] 1.1 Add `llama-index-core`, `llama-index-readers-file`, `llama-index-llms-minimax`, `llama-index-embeddings-huggingface` to `backend/pyproject.toml`; add `torch` as an explicit **direct** dependency (needed even though nothing imports it directly — uv only applies `tool.uv.sources` overrides to direct dependencies, and `torch` otherwise only arrives transitively via `sentence-transformers`); add `[tool.uv.sources]` pinning `torch` to the `pytorch-cpu` index and a matching `[[tool.uv.index]]` block pointing at `https://download.pytorch.org/whl/cpu`, to avoid pulling in the full CUDA/cuDNN/NCCL stack (~5GB vs. ~1.2GB) for a container with no GPU; run `uv sync` and confirm `torch==...+cpu` (not a bare CUDA build) is installed
- [x] 1.2 In `backend/app/config.py`, add a small `_read_secret(name: str) -> str | None` helper: if env var `<NAME>_FILE` is set (or the default `/run/secrets/<name>` exists) and the file is non-empty, read and strip the credential from it; otherwise fall back to the plain `<NAME>` env var (treating an empty value as absent too). Use it for `MINIMAX_API_KEY` (the only credential needed — embeddings are local and need no key)
- [x] 1.3 Add `MINIMAX_LLM_MODEL` (default `MiniMax-M2.7`, the package's own default), `INDEX_DIR` (default `/data/index`), and `HF_HOME` (default `/data/hf-cache`, so the embedding model's download cache is configurable) to `backend/app/config.py` as plain env vars (not secrets)
- [x] 1.4 Create `secrets/.gitkeep` and `secrets/minimax_api_key.txt.example` (placeholder content, e.g. `your-minimax-api-key-here`); add `secrets/*` except `.gitkeep` and `*.example` to `.gitignore`
- [x] 1.5 Document in `AGENTS.md` how to supply the MiniMax API key locally (needed only for `/ask`): copy `secrets/minimax_api_key.txt.example` to `secrets/minimax_api_key.txt` and fill in the real key (recommended), or set `MINIMAX_API_KEY` directly as a fallback env var

## 2. Local embedding model

- [x] 2.1 In `backend/app/rag/index_service.py` (or a small `backend/app/rag/embeddings.py` helper it imports), configure `HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")` as the embedding model used for both indexing and query-time retrieval — no API key or custom wrapper needed
- [x] 2.2 Ensure `HF_HOME` (task 1.3) is set before the embedding model is constructed, so Hugging Face Hub downloads/caches land in the configured (bind-mounted) directory rather than the container's default cache location

## 3. Index service

- [x] 3.1 Create `backend/app/rag/index_service.py` with a module-level singleton index reference and a `threading.Lock` guarding all mutations
- [x] 3.2 Implement `_load_or_create_index()`: load the persisted index from `INDEX_DIR` via `load_index_from_storage` if it exists, otherwise create a new empty index — both paths use the local `HuggingFaceEmbedding` (task 2.1) as the embed model
- [x] 3.3 Implement (inline in `sync_index`) the "already indexed" check: the set of stored filenames present as keys in `index.ref_doc_info`
- [x] 3.4 Implement `_index_file(path, index)`: load one PDF via the PDF reader, set `doc_id`/`ref_doc_id` to its stored filename, and `index.insert()` it — used by both the per-upload path and startup sync
- [x] 3.5 Implement `sync_index()`: acquire the lock, load-or-create the index, diff files in `UPLOAD_DIR` against already-indexed filenames, log the diff (`found`/`already indexed`/`to index` counts), call `_index_file` for each new file (logging per-file success/failure), persist once at the end, and log completion (or "nothing new to index" if the diff was empty)
- [x] 3.6 Implement `index_uploaded_file(path)`: acquire the lock, load-or-create the index if not already in memory, call `_index_file`, persist, and log the outcome for that file
- [x] 3.7 Implement `get_query_engine()`: return a query engine built from the current index using the `llama-index-llms-minimax` LLM, or `None` if no index/documents exist yet
- [x] 3.8 Wrap indexing operations (parsing, embedding calls) in try/except that logs and does not raise past the background task boundary

## 4. Wire indexing into the app lifecycle

- [x] 4.1 In `backend/app/api/uploads.py`, after a successful upload, add a `BackgroundTasks` callback that calls `index_service.index_uploaded_file(path)`
- [x] 4.2 In `backend/app/main.py`, add a lifespan startup handler that schedules `index_service.sync_index()` via `asyncio.create_task(asyncio.to_thread(...))` without blocking startup

## 5. Question-answering endpoint

- [x] 5.1 Create `backend/app/api/ask.py` with `POST /ask` accepting `question: str = Form(...)`
- [x] 5.2 Use `index_service.get_query_engine()` to answer; if no query engine is available (nothing indexed yet), return `{"answer": "No documents have been indexed yet.", "sources": []}`
- [x] 5.3 On MiniMax/config errors, return a clear error response (not a 500 crash) and log the error
- [x] 5.4 Register the `ask` router in `create_app()`
- [x] 5.5 Add tests covering: question answered from a stubbed/mocked query engine, empty-index response, and the missing-API-key error path

## 6. Frontend: wire the ask page

- [x] 6.1 Update `frontend/public/ask/index.html`: change the form to `hx-post="/api/ask"`, remove the `onsubmit="event.preventDefault()"` placeholder, add an `#answer` element
- [x] 6.2 Add a small inline script to parse the JSON response (success or error) via `htmx:afterRequest` and render the answer text (and source filenames if present) into `#answer` using safe DOM text APIs, not `innerHTML`, since the answer text is LLM-generated and must not be treated as trusted markup

## 7. Docker Compose

- [x] 7.1 Bind-mount `./secrets` read-only into the `backend` service at `/run/secrets` in `docker-compose.yml` — **not** Compose's native top-level `secrets:` block, which was found during implementation to hard-fail `docker compose up` (for *every* service, not just backend) if the referenced file doesn't exist yet, breaking the plain-env-var fallback for anyone who hasn't created a secrets file. A bind-mounted directory only requires the directory to exist (via a committed `.gitkeep`), not its contents, so it works whether or not a real secret file is present.
- [x] 7.2 Add `MINIMAX_LLM_MODEL`, `INDEX_DIR`, `HF_HOME`, and `MINIMAX_API_KEY` (sourced from `.env`, defaulting to empty) as backend service environment variables
- [x] 7.3 Add a commented-out `MINIMAX_API_KEY=` line to `.env.example` documenting the plain-env-var fallback, and a `MINIMAX_LLM_MODEL=` line for the model override
- [x] 7.4 Bind-mount `./backend/data/index` into the `backend` service at `INDEX_DIR` (`/data/index`) in `docker-compose.yml`, matching the existing `UPLOAD_DIR` bind mount
- [x] 7.5 Create `backend/data/index/.gitkeep`; add `backend/data/index/*` (except `.gitkeep`) to `.gitignore`
- [x] 7.6 Bind-mount `./backend/data/hf-cache` into the `backend` service at `HF_HOME` (`/data/hf-cache`) in `docker-compose.yml`, so the embedding model download persists across container recreation
- [x] 7.7 Create `backend/data/hf-cache/.gitkeep`; add `backend/data/hf-cache/*` (except `.gitkeep`) to `.gitignore`

## 8. Verification

- [x] 8.1 `uv run pytest -v` — confirm all backend tests pass, including the new ask tests (17/17 passed)
- [x] 8.2 With **no** MiniMax credentials configured at all, `docker compose up --build`; upload a PDF via `/feed/upload` and confirm console logs show background indexing start/complete for it (proving indexing needs no MiniMax key), and that the first embedding call triggers a one-time model download logged/visible in `docker compose logs backend` — confirmed (129MB model cached to `backend/data/hf-cache/`)
- [x] 8.3 Ask a question on `/ask` with no MiniMax key configured; confirm a clear configuration error is shown, not a crash — confirmed, `503` with `"MINIMAX_API_KEY is not configured"`
- [x] 8.4 Put a real key in `secrets/minimax_api_key.txt`, restart the backend; ask a question on `/ask` about the uploaded PDF's content; confirm an answer is displayed, proving the secrets-file path works for `/ask` — confirmed against the real MiniMax API (**found and fixed a real bug here**: the default secret path was missing the `.txt` extension the bind-mounted file actually has; see `design.md` Decision 12)
- [x] 8.5 Ask a question before any upload completes indexing (fresh state); confirm the "no documents indexed yet" response is shown, not an error — covered by `test_ask.py::test_no_documents_indexed_yet`; not re-verified live since re-verifying would require wiping the persisted index in the user's running dev environment
- [x] 8.6 Restart the backend (`docker compose restart backend`); confirm console logs show startup sync reporting the previously uploaded file as already indexed (`0` to index), no model re-download (HF cache bind mount working), and that `/ask` still works afterward without re-embedding it — confirmed
- [x] 8.7 Upload a second PDF, then `docker compose down && docker compose up` (full container recreation, not just restart); confirm both files are still retrievable via `/ask`, console logs show `0` new files to index, and no model re-download — confirmed (used a manually-dropped test PDF as the "second file" — see 8.8)
- [x] 8.8 Manually copy a third PDF directly into `backend/data/uploads/` while the backend is stopped, then start it; confirm startup sync detects and indexes that one new file, logging exactly one file as newly indexed — confirmed (`2 upload(s) found, 1 already indexed, 1 to index`)
- [x] 8.9 Confirm `/ask` works via the plain `MINIMAX_API_KEY` env var fallback (not just the secrets file) — confirmed, tested before the secrets-file fix was in place
