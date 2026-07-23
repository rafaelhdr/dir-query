## Context

`POST /w/<slug>/ask` (`backend/app/api/ask.py`) awaits
`conversations.ask`, which awaits `index_service.answer_question`, which
awaits a single `llm.achat(messages)` call before returning one JSON body
(`AskResponse`). `frontend/nginx.conf`'s `/api/` location has no
`proxy_read_timeout` override, so nginx's 60s default cuts the connection
on slow answers. Both LLM wrappers in use (`MiniMax`, `GoogleGenAI`, via
llama-index) already support `astream_chat`, so streaming is a call-site
change, not a new dependency.

`sources` are derived from the retrieval step (`Chunk`/`File` query),
which completes before the LLM is even called — they're known well before
any answer text exists.

`Exchange.status` is constrained by DB `CheckConstraint` to exactly
`pending` / `answered` / `failed` — no fourth "partial" state exists, and
this design does not add one.

The frontend renders the answer as sanitized Markdown (`marked.js` +
DOMPurify), not plain text, which affects how partial text can be
displayed while streaming.

## Goals / Non-Goals

**Goals:**
- Stream the LLM answer to the browser token-by-token over SSE so the
  connection stays alive and the UI shows real progress.
- Keep generating and persist the full answer even if the client
  disconnects mid-stream.
- Reuse the existing retrieval, prompt-construction, history-loading, and
  `Exchange` persistence logic — only the transport and the LLM call mode
  change.

**Non-Goals:**
- No new `Exchange.status` value (a migration) — disconnect handling reuses
  `answered`/`failed` exactly as today, just reached via a different path.
- No change to which LLM providers are supported, retrieval logic (`TOP_K`,
  cosine distance), or conversation-history loading.
- No general-purpose SSE/streaming framework for other endpoints — this is
  scoped to `/ask`.
- Not adding `EventSource`/native browser SSE — superseded by the
  `fetch()`+`ReadableStream` decision below.

## Decisions

### Transport: `fetch()` + `ReadableStream`, not `EventSource`
`EventSource` is GET-only. The current request is a POST with form data
(`question`, `conversation_id`). Moving those into a query string would
hit URL-length limits on long questions and put question text (which can
reference sensitive document content) into nginx access logs and browser
history. `fetch()` + a hand-rolled SSE frame parser over
`response.body.getReader()` keeps the existing POST body untouched.
(`/ask` has no auth dependency — confirmed via `get_workspace_by_slug`,
which does not check credentials — so the header-vs-cookie auth question
that would otherwise favor `fetch()` doesn't apply here; the POST-body
argument is the deciding one.)

### Endpoint: convert `/ask` in place, not a parallel `/ask/stream`
Only one consumer of `/ask` was found in the repo (the ask page's
`fetch` call). A single code path avoids maintaining duplicate
retrieval+LLM+persistence logic across a JSON version and a streaming
version. This is why the proposal marks the response-shape change as
**BREAKING** rather than additive.

### Generation must survive client disconnect — decouple it from the HTTP response
Starlette's `StreamingResponse` stops driving its generator once it
detects the client disconnected, which would kill in-flight generation if
the LLM call lived inside that generator. Since generation must survive
disconnect (chosen so a user can reopen a conversation and see the
complete answer without re-asking and re-paying for a fresh LLM call, like
ChatGPT), the LLM call and DB persistence run in an independent
`asyncio.create_task`, publishing events to an `asyncio.Queue`. The
route's SSE generator only reads off that queue and forwards events while
the client is connected; if the client goes away, the background task
keeps running to completion untouched.

Alternative considered: let disconnect cancel generation and mark the
exchange `failed`. Rejected — an accidental refresh or nav-away would
waste the generation work already in flight and force a full re-ask.

### Sources sent at the end, not as soon as retrieval finishes
`sources` are known before the LLM call starts, so they could be emitted
as an early SSE event. Decided against it: it changes the current visual
order (answer first, then sources) for a marginal benefit, and holding
them for the final `done` event keeps the frontend's rendering logic
simpler (one metadata payload instead of two).

### SSE event protocol
- `event: token`, `data: <incremental text>` — repeated as the LLM streams.
- `event: done`, `data: {"conversation_id": ..., "title": ..., "sources": [...]}`
  — always the last event on success.
- `event: error`, `data: {"detail": "..."}` — sent if generation fails
  after streaming has already started (can't change HTTP status once
  headers are sent, so this is how errors surface after the first byte).
- The two existing canned-response branches (no documents indexed;
  `NOT_FOUND_ANSWER`) are sent as a single `token` event with the whole
  string, then `done` — same content as today, just wrapped in the
  streaming shape instead of a literal token-by-token feel.
- Errors raised before streaming starts (bad `conversation_id`, missing API
  key) are unaffected — they still return a normal JSON error response
  with the existing status codes (404/503), since headers haven't been
  sent yet at that point.

### Reasoning-tag stripping applied incrementally
`_strip_reasoning` currently regexes `<think>...</think>` out of the full
response once. Applied per-delta, it would leak raw reasoning content into
the visible stream before the closing tag arrives. Instead, keep a
running raw buffer, recompute `_strip_reasoning(raw_buffer)` after each
delta, and emit only the new suffix of the *stripped* text since the last
emission — reasoning content stays invisible throughout, reusing the
existing regex unchanged.

### Frontend: throttled incremental Markdown re-render
Because answers render through `marked.parse()` + DOMPurify (not plain
text), raw partial Markdown mid-token (e.g. an unclosed `**`) would look
broken if displayed as-is. The frontend accumulates the raw text and
re-runs the existing render pipeline on a throttle (~80-100ms), not on
every token, replacing the container's `innerHTML` each time — the same
pipeline used today, just called repeatedly instead of once.

### nginx: `proxy_buffering off` is required, not optional — and scoped to the ask route only
`frontend/nginx.conf`'s `/api/` block has no buffering directives today,
so nginx would buffer the full proxied response before forwarding it,
defeating SSE regardless of what the backend sends. Adding
`proxy_buffering off`, `proxy_http_version 1.1`, and a higher
`proxy_read_timeout` (defense-in-depth, alongside a backend heartbeat
comment sent during idle gaps) is necessary for streaming to actually
reach the browser.

These directives are scoped to a separate regex location matching only
`/api/w/<slug>/ask` (`proxy_pass http://backend:8000/$1` using a capture
group, since regex locations don't get the automatic prefix-replacement
behavior plain prefix locations do), rather than applied to the whole
`/api/` block. Reasoning: the longer `proxy_read_timeout` exists to give
the SSE heartbeat headroom against event-loop stalls (see Risks below);
applying it to every `/api/` endpoint would mean a genuinely hung
non-streaming request (uploads, listings, etc.) also ties up its
connection for up to 300s instead of nginx's normal 60s default, for no
benefit — those endpoints never stream and don't need the heartbeat
headroom. Scoping keeps the blast radius of the longer timeout to the one
route that actually needs it.

## Risks / Trade-offs

- **[Risk]** Background generation on disconnect means an abandoned
  request still consumes LLM API cost with nobody watching.
  → **Mitigation**: Accepted trade-off per the product decision (matches
  ChatGPT-style behavior); no different from today's behavior where a
  disconnect after the request was already sent to the LLM provider still
  gets billed even though the JSON response is discarded.
- **[Risk]** `asyncio.Queue`-based fan-out from a background task to a
  possibly-absent reader is a new concurrency pattern in this codebase.
  → **Mitigation**: Scoped tightly to this one endpoint; the background
  task's only consumer is the queue, and it doesn't need to know or care
  whether anything is reading from it.
- **[Risk]** Any deployment target whose reverse proxy isn't
  `frontend/nginx.conf` (e.g. a different production topology) won't
  automatically get `proxy_buffering off`.
  → **Mitigation**: No such alternate config exists in the repo today
  (confirmed — no `Procfile`/`fly.toml`/k8s ingress/etc. found); backend
  heartbeat comments are defense-in-depth for this scenario regardless.
- **[Risk]** `TestClient`-based tests can't easily simulate a real
  mid-stream socket close.
  → **Mitigation**: test the disconnect-survival behavior by invoking the
  background-task function directly in an async test and asserting DB
  state, rather than trying to fake a socket close through the full HTTP
  stack.

## Migration Plan

No data migration (no schema change). Deploy is a single coordinated
release of backend + frontend + nginx config together, since the frontend
change assumes the backend now returns SSE. Rollback is a plain revert of
that same release — no persisted state depends on the new format.

## Open Questions

None outstanding — transport, disconnect semantics, sources timing, and
rendering strategy were all resolved during grilling before this design
was written.
