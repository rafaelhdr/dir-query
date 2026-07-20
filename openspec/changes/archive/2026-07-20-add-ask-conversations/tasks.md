## 1. Database

- [x] 1.1 Add `Conversation` model to `backend/app/db/models.py` (`id`, `workspace_id` FK to `workspaces.id` `ondelete="CASCADE"`, `title`, `created_at`), with a `workspace` relationship and an index on `workspace_id`.
- [x] 1.2 Add `Exchange` model to `backend/app/db/models.py` (`id`, `conversation_id` FK to `conversations.id` `ondelete="CASCADE"`, `question`, `answer` nullable, `sources` nullable JSON, `status` with `server_default="pending"` and a `CheckConstraint` mirroring `FILE_STATUSES`'s pattern for `("pending", "answered", "failed")`, `created_at`), with a `conversation` relationship and an index on `conversation_id`.
- [x] 1.3 Add a `conversations` relationship on `Workspace` and an `exchanges` relationship on `Conversation`, following the existing `Workspace.files`/`File.chunks` pattern.
- [x] 1.4 Generate the Alembic migration (`alembic revision --autogenerate`) creating `conversations` and `exchanges`, review the generated SQL matches the models, and apply it locally.
- [x] 1.5 Confirm `backend/tests/conftest.py`'s table-truncation list is extended to include `conversations` and `exchanges` so tests stay isolated.

## 2. Answering pipeline

- [x] 2.1 Add `ASK_HISTORY_LIMIT = int(os.getenv("ASK_HISTORY_LIMIT", "10"))` to `backend/app/config.py`, following the same plain-env-var-with-default pattern as `MAX_UPLOAD_BYTES`.
- [x] 2.2 In `backend/app/rag/index_service.py`, add a helper that loads a conversation's exchanges with `status="answered"`, ordered by `created_at`, limited to the most recent `ASK_HISTORY_LIMIT`, and converts each into a `ChatMessage(role=MessageRole.USER, content=question)` / `ChatMessage(role=MessageRole.ASSISTANT, content=answer)` pair.
- [x] 2.3 Change `answer_question` to accept an optional `conversation_id`, build a `ChatMessage` list (system instruction, prior-exchange pairs from 2.2, then the new question + retrieved context as the final user message), and call `llm.achat(messages)` instead of `llm.acomplete(prompt)`.
- [x] 2.4 Keep retrieval unchanged: embed only the raw new question, same `TOP_K` cosine-distance search scoped to the workspace.
- [x] 2.5 Update `_strip_reasoning`/response handling as needed for `achat`'s response shape (a `ChatResponse`, not a plain completion string).
- [x] 2.6 Update or add unit tests in `backend/tests/test_index_service.py` covering: no prior history (behaves like today), history capped at `ASK_HISTORY_LIMIT`, a non-default `ASK_HISTORY_LIMIT` value taking effect, and failed/pending exchanges excluded from the messages sent to the LLM.
- [x] 2.7 Add a case to `backend/tests/test_config.py` for `ASK_HISTORY_LIMIT`'s default and env-var override, matching existing coverage for `MAX_UPLOAD_BYTES`.

## 3. Conversation persistence and endpoints

- [x] 3.1 Add a service function (e.g. in `index_service.py` or a new `backend/app/services/conversations.py`) that: creates a `Conversation` if `conversation_id` is not provided (titled from the question, truncated), inserts an `Exchange` row with `status="pending"`, calls `answer_question`, then updates that row to `status="answered"` (with `answer`/`sources`) or `status="failed"` on exception — returning the conversation id/title alongside the existing `answer`/`sources` shape.
- [x] 3.2 Update `backend/app/api/ask.py`'s `ask_question` to accept `conversation_id: int | None = Form(None)`, call the new service function from 3.1, and include `conversation_id`/`title` in the response. Keep existing error handling (`RuntimeError` → 503, other exceptions → 502) — a failed LLM call should still persist the `failed` exchange (3.1) before the error response is returned.
- [x] 3.3 Add `backend/app/api/conversations.py` with `GET /w/{slug}/conversations` (list, most-recently-active first) and `GET /w/{slug}/conversations/{conversation_id}` (title + ordered exchanges, 404 if not found or not owned by that workspace), both behind `get_workspace_by_slug`.
- [x] 3.4 Register the new router in `backend/app/main.py`'s `create_app()`.
- [x] 3.5 Add `backend/tests/test_conversations.py` covering: creating a conversation via first question, title derivation, listing conversations, fetching a conversation's history including a failed exchange, and the 404 cases.
- [x] 3.6 Update `backend/tests/test_ask.py` for the new request/response shape (`conversation_id` in, `conversation_id`/`title` out), and add a case asserting a failed answer still persists a `failed` exchange.

## 4. Frontend: ask page

- [x] 4.1 Remove the fixed-bottom `.ask-form` positioning in `frontend/public/style.css`; style the form to sit inline in normal document flow instead.
- [x] 4.2 Restructure `frontend/public/w/ask/index.html`'s JS: replace the single `#answer` overwrite with an accumulating list of exchange blocks (question, then loading/answer/error state), each appended to a container, with the form always rendered last.
- [x] 4.3 On submit: append the new question immediately with a loading state, `fetch` `/api/w/<slug>/ask` with `question` and the currently tracked `conversation_id` (if any), then replace that exchange's loading state with the answer/sources or an error, and store the returned `conversation_id` for subsequent submits in the same session.
- [x] 4.4 Add a "New conversation" action that clears the exchange container and drops the tracked `conversation_id`, without any backend call.
- [x] 4.5 Support loading an existing conversation on page load (e.g. via a `?conversation=<id>` query param): fetch `GET /api/w/<slug>/conversations/<id>`, render its full exchange history (including failed ones with an error state) before the form, and set the tracked `conversation_id` so further questions append to it.
- [x] 4.6 Add a link/action on the ask page navigating to the conversation list view (task 5).
- [x] 4.7 Continue using `textContent`/`createElement` (never `innerHTML`) for all LLM-derived and user-derived text, consistent with the existing XSS-safety approach.

## 5. Frontend: conversation list page

- [x] 5.1 Add a new static page (e.g. `frontend/public/w/ask/conversations/index.html`) following the existing SSI-include pattern (`head.html`/`nav.html`/`heading.html`).
- [x] 5.2 Add the corresponding Nginx rewrite in `frontend/nginx.conf` for the new route.
- [x] 5.3 On load, `fetch` `GET /api/w/<slug>/conversations` and render each conversation as a link to the ask page with `?conversation=<id>`, showing title and created-at.
- [x] 5.4 Handle the empty-state case (no conversations yet) with a clear message.

## 6. Spec and documentation cleanup

- [x] 6.1 Run `openspec archive add-ask-conversations` once implementation is complete and verified, to fold the delta specs into `openspec/specs/ask-page/spec.md`, `openspec/specs/question-answering/spec.md`, and create `openspec/specs/conversation-history/spec.md`.
- [x] 6.2 Verify no other page/doc references the old fixed-bottom input behavior (e.g. screenshots, other spec cross-references).

## 7. End-to-end verification

- [x] 7.1 Run `uv run pytest -v` in `backend/` and confirm all tests pass, including new/updated ones.
- [x] 7.2 Manually verify via `docker compose up --build`: ask a question (new conversation created), ask a follow-up referencing the first answer, start a new conversation, reopen the previous conversation from the list and confirm its full history (including a deliberately triggered failed exchange, e.g. by temporarily unsetting the LLM API key) renders correctly. Verified via curl against the live stack with a real MiniMax key (multi-turn follow-up correctly used conversation history); the failed-exchange path is covered by `test_failed_answer_persists_a_failed_exchange`/`test_get_conversation_includes_failed_exchange` since the Chrome extension wasn't available in this environment to click through it visually.
