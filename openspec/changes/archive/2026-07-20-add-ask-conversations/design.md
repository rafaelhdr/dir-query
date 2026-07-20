## Context

`/w/<slug>/ask` currently has no memory: `POST /w/{slug}/ask` (`backend/app/api/ask.py`) takes a bare `question` form field, calls `index_service.answer_question(workspace_id, question)`, and returns `{"answer": ..., "sources": [...]}`. Inside, `answer_question` (`backend/app/rag/index_service.py`) embeds the raw question, runs a `Chunk.embedding.cosine_distance` search scoped to the workspace, builds one flat prompt string, and calls `llm.acomplete(prompt)` — a single-shot completion, not a chat call. Nothing about the question or answer is persisted. The frontend (`frontend/public/w/ask/index.html`) is a single `<form>` with one text input pinned via `.ask-form { position: fixed; bottom: 0; ... }` (`frontend/public/style.css`), submitted with plain `fetch`, and the `#answer` div is cleared and overwritten on every submit.

This change adds a `Conversation`/`Exchange` persistence layer, makes the answering pipeline chat-aware (bounded history), and reworks the ask page into a stacked, growing thread with the input inline instead of fixed. It was scoped through a grilling session with the user; the resulting decisions are recorded below as the source of truth for `tasks.md`.

## Goals / Non-Goals

**Goals:**
- A workspace can have multiple, independently-titled conversations, each with its own persisted exchange history.
- Each question a user asks is visible immediately, with a loading state, and is persisted regardless of whether the LLM call succeeds.
- Reopening a past conversation shows its full history, including failed exchanges.
- The LLM sees up to the last N exchanges of the current conversation as prior turns (N configurable via env var, default 10), so follow-up questions can reference earlier answers.
- The ask page input is no longer viewport-fixed; it sits inline after the latest exchange.

**Non-Goals:**
- No token-by-token streaming. The response is still a single JSON payload returned once the answer is ready; the frontend shows a loading state in between.
- No history-aware query reformulation for retrieval — the vector search embeds only the latest question's raw text, same as today. Multi-turn follow-ups that rely on pronouns/context for retrieval (not just for answer phrasing) may retrieve poorly; accepted for this change.
- No summarization/compaction of history beyond the hard cutoff — older exchanges are simply excluded from what's sent to the LLM (they remain visible in the UI/DB).
- No conversation delete or rename.
- No authentication changes; conversations are scoped by workspace exactly as files/chunks are today (no additional access control).

## Decisions

### 1. Two new tables: `conversations` and `exchanges`
```python
class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), nullable=False)

class Exchange(Base):
    __tablename__ = "exchanges"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(nullable=False)
    answer: Mapped[str | None] = mapped_column(nullable=True)
    sources: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, server_default="pending")  # pending|answered|failed
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), nullable=False)
```
One `Exchange` row per question/answer pair (not per chat-message-role), following the `File.status` lifecycle pattern (`pending`/`indexed`/`failed` → `pending`/`answered`/`failed`) already established in this codebase. `sources` is stored as JSON (a list of `File.display_name` strings) rather than a join table, mirroring how the answer already returns `sources` as a flat list with no need to query it relationally.
- **Alternative considered**: a role-based `Message` table (`role`, `content`, `conversation_id`) mirroring the `ChatMessage` list sent to the LLM. Rejected — decided against in the scoping discussion in favor of fewer rows and a schema that matches how the UI actually renders (one block per exchange, not per message), at the cost of a small transform step (Exchange → alternating user/assistant `ChatMessage`s) when building LLM context.

### 2. Exchange lifecycle: insert on question, update on answer
`POST /w/{slug}/ask` (see Decision 4) writes a `status="pending"` row with `question` set and `answer`/`sources` null *before* calling the LLM, then updates that same row to `status="answered"` (with `answer`/`sources`) or `status="failed"` (answer/sources stay null) once the call resolves. This guarantees every submitted question is persisted even if the LLM call errors or times out, and lets a reopened conversation render a failed exchange as a visible error entry instead of silently dropping it.
- **Alternative considered**: single `INSERT` only after the answer is ready. Rejected — the user's explicit choice was to persist failures visibly, which requires a row to exist before the outcome is known.

### 3. Conversation creation is implicit, on first question
There is no "create conversation" endpoint. `POST /w/{slug}/ask` accepts an optional `conversation_id`; when omitted, a new `Conversation` is created as part of that same request, titled from the question (truncated, e.g. first ~60 characters), and its id is returned in the response so the frontend can adopt it for subsequent questions in that thread. The "New conversation" UI action is purely client-side (clear the current thread state, drop the remembered `conversation_id`) — it never calls the backend by itself.
- **Alternative considered**: an explicit `POST /w/{slug}/conversations` to create a conversation up front. Rejected — would leave orphaned, untitled, empty conversations in the list for every "New conversation" click that isn't followed by a question.

### 4. `POST /w/{slug}/ask` becomes conversation-aware; a new `conversations` router handles listing/fetching
`ask.py` changes its form fields to `question: str = Form(...)`, `conversation_id: int | None = Form(None)`, and its JSON response gains `conversation_id` and `title` alongside `answer`/`sources`. A new `backend/app/api/conversations.py` router adds:
- `GET /w/{slug}/conversations` — list this workspace's conversations (id, title, created_at), most recent first.
- `GET /w/{slug}/conversations/{conversation_id}` — fetch a conversation's title plus its full ordered list of exchanges (including failed ones), for the "reopen" flow.
Both are read-only additions; no new write endpoints beyond the modified `/ask`.

### 5. Answering pipeline: `llm.acomplete(prompt)` → `llm.achat(messages)`, capped history
`answer_question` gains a `conversation_id: int | None` parameter. When present, it loads the conversation's exchanges ordered by `created_at`, takes the most recent `ASK_HISTORY_LIMIT` with `status="answered"` (failed/pending exchanges are excluded from LLM context — there's no useful assistant turn to replay), and converts each into a `ChatMessage(role="user", content=question)` / `ChatMessage(role="assistant", content=answer)` pair (`llama_index.core.llms.ChatMessage`, `MessageRole`). The system instruction (the existing "answer using only the context below" framing) becomes a `ChatMessage(role="system", ...)`, and the final message is `role="user"` containing the new question plus the freshly retrieved chunks for *this* question. The whole list is passed to `llm.achat(messages)` instead of `llm.acomplete(prompt)`. Both `MiniMax` (`OpenAILike`-based) and `GoogleGenAI` llama-index LLM classes already implement `achat`, so this needs no per-provider branching beyond what `_get_llm()` already does.
- Retrieval is unchanged: `embed_model.get_query_embedding(question)` on the raw new question only, same `TOP_K=5` cosine-distance search scoped to the workspace.
- `ASK_HISTORY_LIMIT` (`backend/app/config.py`, `int(os.getenv("ASK_HISTORY_LIMIT", "10"))`) caps how many answered exchanges are sent to the LLM, following the same plain-env-var-with-default pattern as `MAX_UPLOAD_BYTES` (not the validated-choice pattern used for `EMBED_PROVIDER`/`LLM_PROVIDER`, since this is a plain integer, not an enum). Older exchanges beyond the cap are excluded from the message list but remain in the DB and in the conversation-history UI regardless of the configured limit.
- **Alternative considered**: keep `acomplete` and concatenate history into one long prompt string. Rejected — `achat` is already supported by both configured providers and represents conversation turns more faithfully (avoids prompt-injection-flavored ambiguity of string-concatenated turns, and matches how these APIs are meant to be used for multi-turn context).
- **Resolved open question**: the cap is configurable via `ASK_HISTORY_LIMIT` rather than hardcoded — cheap to add (one `os.getenv` line, same shape as `MAX_UPLOAD_BYTES`) and avoids a code change if it needs tuning after real usage.

### 6. Frontend: inline stacked exchanges, one page render per conversation
`frontend/public/w/ask/index.html` changes from a single `#answer` div to a container that accumulates one block per exchange (question text, then either a loading indicator, the answer + sources, or an error state), in submission order. The `<form>` moves out of `.ask-form`'s fixed positioning (that CSS rule is removed) and renders as the last element in the same container, after the most recent exchange, so it's part of normal page flow and shifts down as exchanges accumulate. Opening a conversation from the list view loads `GET /w/{slug}/conversations/{id}` and renders all of its exchanges (including failed ones, shown with an error state) before the form. No client-side state library is introduced — the running list of exchanges is held as a plain in-memory JS array driving DOM creation via `createElement`/`textContent`, consistent with the existing no-`innerHTML` pattern (answer text is LLM-generated/untrusted).
- A new list page (e.g. `frontend/public/w/ask/conversations/index.html`) renders `GET /w/{slug}/conversations` as a list of links; each links to the ask page with a `?conversation=<id>` query param (or similar) that the ask page reads on load to fetch and render that conversation's history instead of starting empty.
- The `ask-page` OpenSpec requirement that hard-codes "positioned at the bottom of the page" is superseded by a MODIFIED requirement describing the inline-after-last-exchange behavior.

## Risks / Trade-offs

- **[Risk]** Capping history at the most recent `ASK_HISTORY_LIMIT` *answered* exchanges means a long conversation's early context silently stops influencing new answers, with no visible signal to the user that this happened. → **Mitigation**: accepted per explicit user decision; the default (10) is generous for a document-Q&A tool's expected conversation lengths, all history remains visible in the UI even though the LLM stops seeing it, and the limit is tunable via env var without a code change if it proves too small.
- **[Risk]** Retrieval still embeds only the raw new question, so pronoun-heavy follow-ups ("what about that?") may retrieve irrelevant chunks even though the chat history gives the LLM enough to phrase a plausible-sounding but ungrounded answer. → **Mitigation**: accepted per explicit user decision; revisit with query reformulation if this proves to be a real problem in practice.
- **[Risk]** `sources` stored as a JSON column (not a relational join to `files`) means a renamed/deleted file's display name in old exchanges won't reflect the change. → **Mitigation**: acceptable — `sources` is a historical record of what was cited at answer time, not a live reference; `File` deletion behavior is unaffected (no FK to enforce).
- **[Risk]** A `pending` exchange left behind by a backend crash mid-request (rather than a clean exception) would be stuck showing a permanent loading/error-less state on reopen. → **Mitigation**: out of scope for this change; the existing `/ask` endpoint already wraps the LLM call in try/except that catches both `RuntimeError` (config) and generic `Exception`, so a `pending` row only survives if the process itself dies mid-request — treated as an acceptable, rare edge case, same class of risk as `File.status` getting stuck at `pending` on a crash during indexing.

## Migration Plan

New Alembic migration adds `conversations` and `exchanges` tables (no backfill — this is new data, no prior questions were ever persisted). Rollout is the normal `docker compose up --build` plus `alembic upgrade head`; rollback drops both tables (no other table gains a dependency on them — `workspaces` and `files`/`chunks` are unaffected). The frontend and backend changes ship together; there's no intermediate state where only one side is deployed, since the `/ask` request/response shape changes on both ends simultaneously.

## Open Questions

None outstanding.
