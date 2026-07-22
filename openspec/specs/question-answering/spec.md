## Purpose

The question-answering capability lets a user ask a natural-language
question, scoped to a workspace, and get an answer generated from the
content of that workspace's indexed documents, using retrieval over the
workspace's chunks in Postgres (joined from `chunks` to their owning
`files` row) and the MiniMax LLM.
## Requirements
### Requirement: Backend endpoint answers questions using the indexed documents
The system SHALL provide a backend endpoint, scoped to a single workspace
(`/w/<slug>/ask`), that accepts a natural-language question, optionally
associated with an existing conversation in that workspace, and SHALL
answer it using retrieval over that workspace's chunks in Postgres
(scoped to the workspace via a join from chunks to their owning file) and
the configured LLM. When the question belongs to a conversation with
prior exchanges, the system SHALL include up to a configurable number of
the most recent previously answered exchanges of that same conversation
(defaulting to 10) as prior conversation turns when generating the
answer, so the LLM can account for what was previously asked and
answered.

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

#### Scenario: A follow-up question can reference an earlier answer
- **WHEN** a user submits a question within a conversation that already
  has one or more previously answered exchanges
- **THEN** the answer is generated using the LLM, including up to the
  configured number of previously answered exchanges of that
  conversation as prior conversation turns, alongside the retrieval
  results for the new question

#### Scenario: Conversation history beyond the configured limit is not sent to the LLM
- **WHEN** a user submits a question within a conversation that already
  has more previously answered exchanges than the configured history
  limit
- **THEN** only the most recent answered exchanges, up to that
  configured limit, are included as prior conversation turns when
  generating the answer

#### Scenario: The history limit defaults to 10 and can be configured
- **WHEN** no history-limit configuration is set for the backend
- **THEN** up to 10 previously answered exchanges are used as prior
  conversation turns, and an operator can change this limit through
  backend configuration without a code change

#### Scenario: A failed or pending exchange is not replayed as conversation history
- **WHEN** a conversation includes an exchange with a status other than
  answered
- **THEN** that exchange is not included among the prior conversation
  turns sent to the LLM for a subsequent question

### Requirement: Question-answering uses a configurable LLM provider, defaulting to MiniMax
The system SHALL generate answer text using whichever LLM provider is
configured via `LLM_PROVIDER` (see the `llm-provider-selection`
capability), via a configured API key for that provider. By default
(`LLM_PROVIDER` unset or `minimax`), this SHALL be the MiniMax API, as
before this capability existed. When the workspace being asked has a
dedicated key configured (see the `workspace-llm-key-selection`
capability), the system SHALL use that workspace's dedicated provider and
credential instead of the globally configured `LLM_PROVIDER` and its
credential.

#### Scenario: Asking a question without a configured API key for the selected provider
- **WHEN** a user submits a question to a workspace using the system key
  while the backend has no valid API key configured for the currently
  selected `LLM_PROVIDER` (MiniMax or Gemini)
- **THEN** the endpoint returns a clear error response and does not crash
  the backend process

#### Scenario: Asking a question using the Gemini LLM provider
- **WHEN** a user submits a question to a workspace using the system key
  while `LLM_PROVIDER=gemini` and a valid `GOOGLE_API_KEY` is configured
- **THEN** the endpoint returns an answer generated using the Gemini API

#### Scenario: Asking a question in a workspace with a dedicated key
- **WHEN** a user submits a question to a workspace whose `key_source` is
  `dedicated`
- **THEN** the endpoint generates the answer using that workspace's
  configured provider and credential, regardless of the backend's globally
  configured `LLM_PROVIDER`

### Requirement: Each answered exchange records which key source and provider answered it
The system SHALL record, on each successfully answered exchange, which key
source (`system` or `dedicated`) and which provider (`gemini` or `minimax`)
generated its answer, reflecting the workspace's key configuration at the
moment that exchange was answered.

#### Scenario: Exchange answered using the system key
- **WHEN** a question is answered in a workspace using the system key
- **THEN** the resulting exchange records `system` as its key source and
  the provider that answered it

#### Scenario: Exchange answered using a dedicated key
- **WHEN** a question is answered in a workspace using a dedicated key
- **THEN** the resulting exchange records `dedicated` as its key source and
  the workspace's configured provider
</content>

