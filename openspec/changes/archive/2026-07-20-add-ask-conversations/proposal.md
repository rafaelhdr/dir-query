## Why

The ask page currently answers each question in isolation: nothing is
persisted, the LLM sees no prior turns, and the input is fixed to the
bottom of the page regardless of how the answer is displayed. Users
asking a follow-up question get no benefit from what they already asked,
and there is no way to come back later and see what was previously asked
in a workspace. This change makes asking questions a real, persisted,
multi-turn conversation.

## What Changes

- **BREAKING**: The ask page input is no longer fixed to the bottom of
  the viewport. It now sits inline in the page flow, directly after the
  most recent question/answer exchange, and moves down the page as the
  conversation grows.
- A workspace can now have multiple named conversations. A "New
  conversation" action resets the page to an empty thread; the
  `Conversation` record itself is only created once the first question in
  it is actually asked, titled from that question's text.
- Each question/answer pair is persisted as an `Exchange` row
  (`conversation_id`, `question`, `answer`, `sources`, `status`,
  `created_at`). A row is written when the question is submitted
  (`status=pending`, no answer yet) and updated once the backend responds
  (`status=answered` with the answer and sources, or `status=failed` with
  no answer). Failed exchanges remain visible in history.
- A workspace gets a conversation list view (separate page, not a
  sidebar) showing past conversations by title and date; opening one
  loads its full exchange history, including any failed exchanges.
- The backend `/w/<slug>/ask` answering pipeline moves from a single-shot
  completion call to a chat-style call that includes up to the last N
  exchanges of the current conversation as prior turns (N configurable
  via the `ASK_HISTORY_LIMIT` env var, default 10), so answers can
  reference what was asked before. Retrieval (embedding + vector search)
  still uses only the latest question's text — no query reformulation
  using history.
- Answers are still returned as a single response once complete; no
  token-by-token streaming is introduced.

## Capabilities

### New Capabilities
- `conversation-history`: Persisting conversations and their exchanges,
  listing a workspace's past conversations, reopening one to view its
  full history (including failed exchanges), and the pending/answered/
  failed exchange lifecycle.

### Modified Capabilities
- `ask-page`: Input moves from fixed-at-bottom to inline-after-last-
  exchange; adds a "New conversation" action and navigation to the
  conversation list view; multiple exchanges render in sequence on one
  page load when reopening a conversation.
- `question-answering`: The backend endpoint becomes conversation-scoped
  (operates within a `Conversation`, not just a workspace), includes up
  to a configurable number (default 10) of prior exchanges of that
  conversation as chat history when generating an answer, and persists
  each exchange (pending → answered/failed) as part of answering.

## Impact

- **Database**: new `conversations` and `exchanges` tables, new Alembic
  migration. `exchanges.conversation_id` FKs to `conversations.id`;
  `conversations.workspace_id` FKs to `workspaces.id`.
- **Backend**: `backend/app/api/ask.py` (request/response shape changes
  to include `conversation_id`), likely a new `backend/app/api/
  conversations.py` router (list/create-on-first-question/fetch), new
  SQLAlchemy models in `backend/app/db/models.py`, and
  `backend/app/rag/index_service.py`'s `answer_question` switches from
  `llm.acomplete(prompt)` to `llm.achat(messages)` with history assembly.
- **Frontend**: `frontend/public/w/ask/index.html` restructured for
  inline input + multiple stacked exchanges; new conversation list page
  under `frontend/public/w/ask/` (or similar); `style.css` updates
  removing the fixed-bottom `.ask-form` positioning. Stays framework-free
  (plain HTML/vanilla JS/htmx), per `AGENTS.md`.
- **Specs**: `openspec/specs/ask-page/spec.md` and
  `openspec/specs/question-answering/spec.md` both need delta updates;
  new `openspec/specs/conversation-history/spec.md`.
