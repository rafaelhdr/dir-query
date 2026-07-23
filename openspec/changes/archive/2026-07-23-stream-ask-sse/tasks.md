## 1. Backend: streaming generation in `index_service.py`

- [x] 1.1 Change the LLM call in `answer_question` from `await
      llm.achat(messages)` to `llm.astream_chat(messages)` and turn the
      function into an async generator.
- [x] 1.2 Yield `{"type": "token", "text": <delta>}` events as chunks
      arrive; for the two canned-response branches (no documents indexed,
      `NOT_FOUND_ANSWER`), yield one `token` event with the full string.
- [x] 1.3 Apply `_strip_reasoning` incrementally: keep a running raw
      buffer, recompute the stripped text after each delta, and only
      yield the new suffix since the last emission, so `<think>` content
      never reaches an emitted event.
- [x] 1.4 Yield a final `{"type": "final", "answer": ..., "sources": ...,
      "llm_key_source": ..., "llm_provider": ...}` event once the stream
      completes. (Errors are propagated as exceptions and turned into an
      `error` event one layer up, in `conversations.py`'s background task,
      rather than inside `answer_question` itself — keeps error-formatting
      in one place alongside the persistence/failed-status logic that
      already needs to react to it.) `sources` is still computed from
      retrieval exactly as today. Also required moving `_get_llm`'s
      workspace/key lookup out into a new `resolve_llm()` called eagerly
      by `conversations.ask` before the background task starts, so a
      missing API key still surfaces as an HTTP 503 raised before any
      streaming response begins (see design note in `conversations.py`).

## 2. Backend: decouple generation from the HTTP response in `conversations.py`

- [x] 2.1 In `ask`, after creating the `pending` `Exchange` (unchanged),
      spawn `asyncio.create_task(...)` that iterates
      `index_service.answer_question(...)`, forwards each event onto an
      `asyncio.Queue`, and on `final`/`error` persists the `Exchange`
      (`answer`, `sources`, `status`, `llm_key_source`, `llm_provider`)
      exactly as the current inline logic does.
- [x] 2.2 Ensure this task is not cancelled by request/connection
      teardown — it must run to completion and persist regardless of
      whether anything is still reading the queue. Done via a
      module-level `_background_tasks` set holding a strong reference
      (plain `asyncio.create_task` isn't tied to the request's lifecycle,
      but needs a strong ref or it can be GC'd mid-flight).
- [x] 2.3 Return the raw queue (not an async-generator wrapper — see
      below) plus `conversation_id`/`title` to the route so streaming can
      start immediately.
- [x] 2.4 Keep existing exception handling: `ConversationNotFoundError`
      still raised synchronously before the background task starts (bad
      `conversation_id` check happens up front, unchanged).

## 3. Backend: SSE route in `ask.py`

- [x] 3.1 Return `StreamingResponse(..., media_type="text/event-stream")`
      wrapping a generator that reads off the queue from step 2 and
      formats each event as an SSE frame (`event: token`/`done`/`error`
      plus `data: ...`, JSON-encoded so embedded newlines can't break SSE
      framing).
- [x] 3.2 Send an SSE comment heartbeat (`: keep-alive\n\n`) if no event
      arrives within ~15s while waiting on the queue, via
      `asyncio.wait_for(queue.get(), timeout=15)` directly on the queue
      (not on a wrapping async generator — see note on task 2.3:
      `Queue.get()` cancellation from a `wait_for` timeout is safe to
      retry, but cancelling a suspended async generator's `__anext__()`
      closes it permanently on the first timeout).
- [x] 3.3 Keep the existing `ConversationNotFoundError` → 404 and
      `RuntimeError` → 503 JSON error responses for failures that happen
      before the stream starts (unchanged from today).
- [x] 3.4 On failure after the stream has started, emit an `event: error`
      SSE frame instead of changing the HTTP status (headers already
      sent).

## 4. Infra: nginx SSE support

- [x] 4.1 Added `proxy_buffering off;`, `proxy_http_version 1.1;`,
      `proxy_set_header Connection "";`, and a higher `proxy_read_timeout`
      (`300s`, defense-in-depth) in `frontend/nginx.conf` — scoped to a
      dedicated regex location matching only `/api/w/<slug>/ask`
      (`location ~ ^/api/(w/[^/]+/ask)$`, `proxy_pass
      http://backend:8000/$1`), not the whole `/api/` block, so the longer
      timeout doesn't apply to non-streaming endpoints that don't need it.
      Verified with `nginx -t` plus live requests: the ask route still
      streams correctly and a regular `/api/workspaces/...` request still
      comes back with a normal buffered `Content-Length` response.

## 5. Frontend: SSE consumption in `w/ask/index.html`

- [x] 5.1 Replace the `fetch(...).then(r => r.json())` flow with
      `fetch()` + `response.body.getReader()`, decoding chunks with
      `TextDecoder` and splitting on blank lines into SSE frames.
- [x] 5.2 Parse `event:`/`data:` lines from each frame into `{type,
      data}` (`parseSseFrame`).
- [x] 5.3 On `token`: append to an accumulated string; re-render via the
      existing `renderMarkdown` + DOMPurify pipeline on a throttle
      (~80ms), replacing the container's `innerHTML`.
- [x] 5.4 On `done`: do one final authoritative re-render using the
      event's `answer` (not just the accumulated tokens — the backend can
      canonicalize the final text, e.g. the "not found" answer, only once
      generation completes), render `sources` via the existing loop, keep
      the existing `history.replaceState` first-question URL update.
- [x] 5.5 On `error` event or non-`response.ok` status: reuse the
      existing `showError()`.
- [x] 5.6 Keep the "Thinking…" loading state until the first `token`
      frame arrives; keep the existing input/button disable + `finally`
      re-enable wrapping the new read loop.

## 6. Tests

- [x] 6.1 Update the `answer_question` monkeypatch stub in
      `backend/tests/test_ask.py` to an async generator yielding `token`
      then `final` events, matching the new interface. Also discovered
      during verification (task 7.5): `backend/tests/test_conversations.py`
      and `backend/tests/test_index_service.py` call/stub
      `answer_question`/`resolve_llm` directly too and needed the same
      treatment — not just `test_ask.py`. All three updated.
- [x] 6.2 Update route-level tests to consume the stream. Used
      `TestClient`'s plain `client.post(...)` (not `.stream(...)`) since
      Starlette's `TestClient` already fully drains a streaming response
      into `response.text` before returning — a small `_parse_sse_events`/
      `_done_event` helper reconstructs the frames from that text. Assertions
      unchanged in substance (`answer`, `sources`, `conversation_id`, DB
      `status`).
- [x] 6.3 Added
      `test_generation_completes_and_persists_even_if_nothing_reads_the_queue`
      in `test_ask.py`: calls `conversations.ask` directly, never reads the
      returned queue, awaits the background task found via
      `conversations._background_tasks`, and asserts the `Exchange` ends up
      `status == "answered"` with the full answer.
- [x] 6.4 Full suite passes (117/117) after also fixing
      `test_conversations.py`/`test_index_service.py` (see 6.1). Failure-path
      assertions unchanged in substance (missing API key → 503, bad
      `conversation_id` → 404, no-documents-indexed, not-found-answer,
      `Exchange.status == "failed"` on error) — the missing-key case now
      monkeypatches `resolve_llm` instead of `answer_question` directly,
      since that's where `_get_llm` moved to (see task 1.4's note).

## 7. Verification

Browser automation (Chrome extension) wasn't available this session, so
verification 7.1/7.2/7.3/7.4 was done against the real running stack
(`docker compose up --build`, rebuilt to pick up the nginx.conf change)
via `curl -N` against `http://localhost:8080/api/...` — same nginx +
backend path the browser would use, just without the DOM/JS layer.

- [x] 7.1 Asked real questions against an existing indexed workspace
      through the live stack; got back multiple `event: token` SSE frames
      with genuinely incremental text (confirmed via `curl -w
      '%{time_starttransfer}/%{time_total}'`: first byte at 0.23s, full
      response at 4.24s — data arrived progressively, not as one blob).
      **Found and fixed a real bug in the process**: the initial
      `_strip_reasoning`-based re-diff approach leaked raw `<think>...`
      reasoning content in the first token event, because a regex over the
      accumulated buffer can't match an unclosed `<think>` tag. Replaced it
      with a proper streaming state machine (`_ReasoningFilter` in
      `index_service.py`) that tracks in-think state across chunks and
      holds back partial-tag boundaries. Re-verified live: no more leaked
      reasoning content. Full backend suite re-run after the fix: 117/117
      still pass.
- [x] 7.2 Confirmed via response headers over the real nginx proxy:
      `Content-Type: text/event-stream; charset=utf-8`,
      `Transfer-Encoding: chunked`, no `Content-Length` (which would
      indicate nginx buffered the full response before forwarding).
- [x] 7.3 Sent a request for a long answer with `timeout 1 curl` (kills
      the TCP connection ~1s in, well before generation finishes), then
      polled the DB directly: the exchange ended up `status = "answered"`
      with a 5791-character answer, confirming generation and persistence
      completed entirely server-side after the client was gone.
- [x] 7.4 Verified live: empty workspace → single `token` event with
      "No documents have been indexed yet." then `done`, same SSE shape as
      a normal streamed answer.
- [x] 7.5 Ran the full suite locally (`uv run pytest`, matching AGENTS.md's
      documented flow — the `backend/tests/` directory isn't volume-mounted
      into the `backend` container per `docker-compose.yml`, so `docker
      compose exec backend uv run pytest` can't see the test files; ran
      host-side against the `_test` database instead, migrated per
      AGENTS.md's instructions). 117/117 passed.
