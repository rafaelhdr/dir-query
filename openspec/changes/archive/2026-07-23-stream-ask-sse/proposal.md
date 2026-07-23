## Why

`/w/<slug>/ask` currently waits for the entire LLM answer before returning
one JSON response. `frontend/nginx.conf` proxies `/api/` with no
`proxy_read_timeout` override, so nginx's stock 60s default silently kills
the connection on slower answers, and the user just sees a failed request
with no partial progress. Streaming the answer token-by-token over SSE
keeps the connection alive (bytes keep flowing, resetting the read-timeout
clock) and gives the UI real incremental rendering instead of a long
"Thinking…" stall followed by an all-or-nothing flash or a timeout error.

## What Changes

- **BREAKING**: `POST /w/<slug>/ask` now returns `Content-Type:
  text/event-stream` (SSE) instead of a single JSON body. The response is a
  stream of `token` events (incremental answer text), followed by one
  `done` event carrying `conversation_id`, `title`, and `sources`, or an
  `error` event on failure.
- Backend LLM calls switch from `achat` (blocking, full response) to
  `astream_chat` (both `MiniMax` and `GoogleGenAI` llama-index wrappers
  already support this — no new dependency).
- If the browser disconnects mid-stream, the backend keeps generating the
  answer in the background and persists it in full — reopening the
  conversation later shows the complete answer even though nothing was
  streamed to the (now gone) client.
- `frontend/public/w/ask/index.html` switches from `fetch().then(r =>
  r.json())` to `fetch()` + `ReadableStream` reading, parsing SSE frames and
  incrementally re-rendering the accumulated Markdown answer as tokens
  arrive (throttled), instead of swapping in the full answer at once.
- `frontend/nginx.conf`'s `/api/` location gets `proxy_buffering off`
  (required for SSE to actually stream through nginx rather than being
  buffered) plus `proxy_http_version 1.1` and a higher `proxy_read_timeout`
  as defense-in-depth.
- Reasoning-model `<think>...</think>` stripping (`_strip_reasoning`) is
  applied incrementally so hidden reasoning content never reaches the
  client, not just at the end.

## Capabilities

### New Capabilities
(none — this extends two existing capabilities' requirements)

### Modified Capabilities
- `question-answering`: the backend endpoint's response shape changes from
  one JSON body to an SSE token stream, and a new requirement covers
  generation surviving client disconnect.
- `ask-page`: the "submits questions and displays the answer" requirement
  changes from an atomic loading→answer swap to progressive token-by-token
  rendering while the response streams in.

## Impact

- `backend/app/api/ask.py` — route returns `StreamingResponse` instead of
  `AskResponse`.
- `backend/app/services/conversations.py` — `ask` spawns a background task
  that streams from the LLM and persists the `Exchange` independently of
  the HTTP response lifecycle.
- `backend/app/rag/index_service.py` — `answer_question` becomes an async
  generator using `astream_chat` instead of `achat`.
- `frontend/public/w/ask/index.html` — SSE parsing + incremental Markdown
  rendering.
- `frontend/nginx.conf` — `proxy_buffering off` and related directives on
  `/api/`.
- `backend/tests/test_ask.py` — stub and assertions updated for the
  streaming interface; existing status-code/persistence assertions
  unchanged in substance.
