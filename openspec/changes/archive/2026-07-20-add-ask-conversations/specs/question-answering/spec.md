## MODIFIED Requirements

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
