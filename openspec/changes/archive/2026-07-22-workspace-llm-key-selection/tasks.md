## 1. Dependencies and configuration

- [x] 1.1 Add `cryptography` to `backend/pyproject.toml` and run `uv sync`
- [x] 1.2 Add `WORKSPACE_KEY_ENCRYPTION_SECRET` resolution to `app/config.py` via the existing `_read_secret()` helper, and add `secrets/workspace_key_encryption_secret.txt.example`
- [x] 1.3 Document the new secret in `AGENTS.md` alongside `JWT_SECRET_KEY`/`MINIMAX_API_KEY`/`GOOGLE_API_KEY`

## 2. Encryption helper

- [x] 2.1 Add an encryption module (e.g. `app/services/crypto.py`) that derives a Fernet key from `WORKSPACE_KEY_ENCRYPTION_SECRET` via `base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())`, and exposes `encrypt(plaintext: str) -> str` / `decrypt(ciphertext: str) -> str`
- [x] 2.2 Make `encrypt()` raise a clear `RuntimeError` when the secret isn't configured (mirroring the `RuntimeError("... is not configured")` pattern in `index_service.py`)

## 3. Data model and migration

- [x] 3.1 Add `description`, `key_source`, `key_provider`, `encrypted_api_key` columns to `Workspace` in `app/db/models.py`, with `KEY_SOURCES = ("system", "dedicated")` and `KEY_PROVIDERS = ("gemini", "minimax")` tuples and matching `CheckConstraint`s, following the `FILE_STATUSES`/`EXCHANGE_STATUSES` convention
- [x] 3.2 Add `llm_key_source`, `llm_provider` nullable columns to `Exchange` in `app/db/models.py` (reuse `KEY_SOURCES`/`KEY_PROVIDERS` constraints)
- [x] 3.3 Generate an Alembic migration (`cd backend && uv run alembic revision --autogenerate -m "add workspace key selection"`) and verify the generated SQL matches the design (additive columns, safe defaults, check constraints)
- [x] 3.4 Apply the migration locally and to the `_test` database, confirm `uv run alembic upgrade head` succeeds on both

## 4. Workspace creation API

- [x] 4.1 Add `description`, `key_source`, `key_provider`, `api_key` form fields to `POST /workspaces` in `app/api/workspaces.py`, defaulting `description` to `""` and `key_source` to `"system"`
- [x] 4.2 Validate: reject with 400 when `key_source="dedicated"` and `key_provider` or `api_key` is missing/blank
- [x] 4.3 On dedicated creation, encrypt `api_key` via the crypto helper and store the result in `encrypted_api_key`; surface a clear 503-style error (not a crash) if the encryption secret isn't configured
- [x] 4.4 Update `WorkspacePublic` in `app/schemas.py` to add `description: str` (always populated) and `key_source: str | None` / `key_provider: str | None` (populated only when `can_edit` is true for the requester, else `None`)
- [x] 4.5 Update `_workspace_public()` in `app/api/workspaces.py` to populate the new fields per the `can_edit` gating, for both `list_workspaces` and `get_workspace`

## 5. Question-answering provider resolution

- [x] 5.1 Add a lookup (e.g. in `app/rag/index_service.py` or a small workspace-lookup helper) that loads a workspace's `key_source`/`key_provider`/`encrypted_api_key` and decrypts the credential when dedicated
- [x] 5.2 Change `_get_llm()` in `app/rag/index_service.py` to accept the resolved workspace key config and, when `key_source == "dedicated"`, construct `GoogleGenAI`/`MiniMax` using the workspace's provider and decrypted key (same `GEMINI_LLM_MODEL`/`MINIMAX_LLM_MODEL` model names); otherwise keep today's global-config behavior
- [x] 5.3 Thread the resolved `key_source`/`key_provider` through `answer_question()`'s return value so the caller can record it on the `Exchange`
- [x] 5.4 Confirm `_get_embed_model()` and all indexing/embedding code paths are untouched by this change (dedicated keys apply only to `/ask`)

## 6. Exchange snapshot

- [x] 6.1 Update `app/services/conversations.ask()` to write `llm_key_source`/`llm_provider` onto the `Exchange` row from the value returned by `index_service.answer_question()` when marking it `answered`
- [x] 6.2 Decided not to add `llm_key_source`/`llm_provider` to `ExchangePublic`: `GET /w/{slug}/conversations/{id}` has no ownership check (any visitor with the slug can view exchanges), so exposing it there would leak the owner-only `key_source`/`key_provider` info to non-owners, contradicting the owner-only exposure rule already enforced on `WorkspacePublic`. The fields stay recorded on `Exchange` for internal/debugging use only.

## 7. Frontend: workspace creation form

- [x] 7.1 Add a `description` `<textarea>` to `frontend/public/workspaces/new/index.html`
- [x] 7.2 Add a collapsed `<details>` "Advanced" section containing the System/Dedicated radio with the free-but-limited / charged-to-your-account explanatory text
- [x] 7.3 Add the Gemini/MiniMax radio and a single password-masked credential input, shown only when Dedicated is selected, with label/placeholder text that updates with the provider choice
- [x] 7.4 Wire the new fields into the existing `hx-post="/api/workspaces"` form submission and its `htmx:afterRequest` error handling

## 8. Frontend: workspaces list

- [x] 8.1 Update `frontend/public/workspaces/index.html` to render each workspace's `description` below its title using `marked.parse()` + `DOMPurify.sanitize()`, matching the ask page's rendering pattern, skipping rendering entirely when the description is empty

## 9. Tests

- [x] 9.1 `backend/tests/test_workspaces.py`: creating a workspace with a description; creating with `key_source=dedicated` (valid and missing-credential/provider cases); `key_source`/`key_provider` present for the owner and absent for non-owners/other visitors; description always present and defaults to `""`
- [x] 9.2 A test verifying the stored `encrypted_api_key` is not the plaintext value and is never present in any API response
- [x] 9.3 `backend/tests/test_index_service.py`: asking a question in a dedicated-key workspace uses the workspace's provider/credential instead of global config (mock the LLM client construction); asking in a system-key workspace is unchanged
- [x] 9.4 `backend/tests/test_ask.py`: an answered exchange records `llm_key_source`/`llm_provider` matching the workspace's configuration at ask time
- [x] 9.5 Run the full backend suite (`uv run pytest -v`) and confirm no regressions (116 passed)

## 10. Docs

- [x] 10.1 Update `AGENTS.md`'s LLM/embedding provider section (or add a short new section) documenting per-workspace dedicated keys and the new secret (done in 1.3, alongside the secret's introduction)
