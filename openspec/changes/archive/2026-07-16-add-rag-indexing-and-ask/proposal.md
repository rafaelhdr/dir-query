## Why

Uploaded PDFs currently just sit on disk — nothing reads or understands them, and the `/ask` page is a non-functional placeholder. To deliver on the project's core promise (asking questions about your own documents), uploaded files need to be indexed into a retrievable form, and the ask flow needs to actually answer questions using that index.

## What Changes

- After a file is successfully uploaded, the backend triggers indexing of that file **in the background** (the upload request still returns immediately with the existing success response).
- Indexing uses [llama-index](https://www.llamaindex.ai/) to build a vector index over uploaded PDFs. Embeddings use a local model (no external API needed for indexing); MiniMax is used for the LLM that answers questions. (MiniMax's public API does not currently document an embeddings endpoint, so a local model is used instead — see `design.md`.)
- The index is persisted to disk, bind-mounted to the host so it survives container restarts. On every backend startup, the system syncs the index against the upload folder — indexing any file that isn't already indexed, without re-embedding files that are (so a `docker compose down && up` with no new uploads costs nothing).
- There is no UI showing indexing progress in this change. Indexing start/finish (and startup sync start/finish) are reported via console log output only.
- Add a backend endpoint that answers a user's question using the persisted RAG index and the MiniMax LLM.
- **BREAKING**: the `/ask` page changes from a non-functional placeholder to a working page — submitting a question now calls the backend and displays the answer. This overturns the "Ask page is a non-functional placeholder" requirement introduced in the previous change.
- The MiniMax API key (needed only for `/ask`, not for indexing) is supplied via a Docker Compose file-based secret (recommended) with a plain environment variable as a fallback — not hardcoded or required to sit in `.env`.

## Capabilities

### New Capabilities
- `document-indexing`: background indexing of uploaded PDFs into a disk-persisted (bind-mounted) llama-index vector index (local embeddings, no external API needed), with an incremental sync against the upload folder on every backend startup (only new files are indexed), and console-only progress logging.
- `question-answering`: a backend endpoint that answers a natural-language question using the persisted RAG index and the MiniMax LLM.

### Modified Capabilities
- `ask-page`: the "Ask page is a non-functional placeholder" requirement is replaced — the page now submits the question to the backend and displays the returned answer.

## Impact

- `backend/`: new `app/rag/` package (index building/persistence, local embedding config, query engine), new `POST /ask` endpoint, upload endpoint triggers background indexing, startup hook triggers incremental sync.
- `docker-compose.yml` / `backend/data/index/`: new bind mount for the persisted index (gitignored, like `backend/data/uploads/`).
- `docker-compose.yml` / `backend/data/hf-cache/`: new bind mount for the local embedding model's download cache, so it isn't re-fetched from Hugging Face on every container recreation.
- `backend/pyproject.toml`: new dependencies (`llama-index-core`, `llama-index-readers-file`, `llama-index-llms-minimax`, `llama-index-embeddings-huggingface`), plus a direct `torch` dependency pinned to CPU-only wheels via `[tool.uv.sources]`/`[[tool.uv.index]]` (needed for uv's source override to apply — `torch` is otherwise only a transitive dependency).
- `docker-compose.yml`: new top-level `secrets:` block for `MINIMAX_API_KEY`, mounted into the backend service; `MINIMAX_LLM_MODEL` / `INDEX_DIR` / `HF_HOME` as plain env vars.
- `secrets/`: new gitignored directory holding the local secret file, with a committed `.example` placeholder.
- `frontend/public/ask/index.html`: wired to `POST /api/ask` via htmx, displaying the answer inline.
- `AGENTS.md`: documents how to supply MiniMax credentials locally.
- No changes to `document-upload` or `home-page` capabilities.
