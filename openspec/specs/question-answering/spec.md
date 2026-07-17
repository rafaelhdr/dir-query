## Purpose

The question-answering capability lets a user ask a natural-language
question, scoped to a workspace, and get an answer generated from the
content of that workspace's indexed documents, using retrieval over the
workspace's chunks in Postgres (joined from `chunks` to their owning
`files` row) and the MiniMax LLM.

## Requirements

### Requirement: Backend endpoint answers questions using the indexed documents
The system SHALL provide a backend endpoint, scoped to a single workspace
(`/w/<slug>/ask`), that accepts a natural-language question and SHALL
answer it using retrieval over that workspace's chunks in Postgres
(scoped to the workspace via a join from chunks to their owning file) and
the MiniMax LLM.

#### Scenario: Answering a question about indexed content
- **WHEN** a user submits a question to a workspace that relates to
  content from a document indexed in that same workspace
- **THEN** the endpoint returns an answer generated using retrieved
  content from that workspace's chunks

#### Scenario: No documents indexed yet in this workspace
- **WHEN** a user submits a question to a workspace before any document
  has been successfully indexed in that workspace
- **THEN** the endpoint returns a clear response indicating no documents
  are available yet, rather than an error

#### Scenario: A question is answered only from its own workspace
- **WHEN** a workspace has no indexed content but another workspace does
  have indexed content covering the question's topic
- **THEN** the endpoint for the first workspace returns a response
  indicating no documents are available yet, without using the other
  workspace's content

#### Scenario: Asking a question for a nonexistent workspace
- **WHEN** a user submits a question to a slug that does not correspond to
  any existing workspace
- **THEN** the endpoint responds with a 404 error

### Requirement: Question-answering uses a configurable LLM provider, defaulting to MiniMax
The system SHALL generate answer text using whichever LLM provider is
configured via `LLM_PROVIDER` (see the `llm-provider-selection`
capability), via a configured API key for that provider. By default
(`LLM_PROVIDER` unset or `minimax`), this SHALL be the MiniMax API, as
before this capability existed.

#### Scenario: Asking a question without a configured API key for the selected provider
- **WHEN** a user submits a question while the backend has no valid API key
  configured for the currently selected `LLM_PROVIDER` (MiniMax or Gemini)
- **THEN** the endpoint returns a clear error response and does not crash
  the backend process

#### Scenario: Asking a question using the Gemini LLM provider
- **WHEN** a user submits a question while `LLM_PROVIDER=gemini` and a
  valid `GOOGLE_API_KEY` is configured
- **THEN** the endpoint returns an answer generated using the Gemini API
</content>
