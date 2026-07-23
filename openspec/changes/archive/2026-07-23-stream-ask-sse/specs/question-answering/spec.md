## ADDED Requirements

### Requirement: Backend streams the answer incrementally over SSE
The system SHALL stream the generated answer to the client as a sequence
of Server-Sent Events as text becomes available from the LLM, rather than
waiting for the complete answer before responding, so the client can
render progress incrementally. The final event of a successful stream
SHALL carry the conversation id, conversation title, and sources.

#### Scenario: Answer streams token by token
- **WHEN** a user submits a question that receives a normal
  LLM-generated answer
- **THEN** the endpoint sends the answer as a series of incremental text
  events as the LLM generates it, followed by a final event containing
  the conversation id, title, and sources

#### Scenario: A fixed response is still sent through the same stream shape
- **WHEN** the answer is a fixed response (no documents indexed in the
  workspace yet, or the answer isn't found in the retrieved context)
- **THEN** the endpoint sends that fixed text as one event followed by
  the final event, using the same event shape as a normal streamed answer

#### Scenario: Reasoning content is never streamed to the client
- **WHEN** the configured LLM's raw output includes reasoning content
  wrapped in `<think>` tags
- **THEN** that reasoning content is stripped from every event emitted
  during the stream and never reaches the client, matching the stripping
  already applied to non-streamed answers

### Requirement: Answer generation continues after client disconnect
The system SHALL continue generating an answer and SHALL persist the
resulting exchange (answer, sources, status, key source, provider) even
if the client disconnects before the stream completes.

#### Scenario: Client disconnects mid-stream
- **WHEN** a user's browser disconnects (navigates away, closes the tab,
  or loses network) before an in-progress answer finishes streaming
- **THEN** the backend continues generating the answer and, once
  complete, persists it to the exchange exactly as if the client had
  stayed connected

#### Scenario: Reopening after a disconnect shows the completed answer
- **WHEN** a user reopens a conversation whose most recent exchange was
  still being generated when the client previously disconnected, after
  generation has since finished server-side
- **THEN** the reopened conversation shows the full completed answer for
  that exchange
