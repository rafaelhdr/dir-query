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

### Requirement: Question-answering uses MiniMax for completions
The system SHALL use the MiniMax API (via a configured API key) to generate the answer text.

#### Scenario: Asking a question without a configured MiniMax API key
- **WHEN** a user submits a question while the backend has no valid MiniMax API key configured
- **THEN** the endpoint returns a clear error response and does not crash the backend process
</content>
