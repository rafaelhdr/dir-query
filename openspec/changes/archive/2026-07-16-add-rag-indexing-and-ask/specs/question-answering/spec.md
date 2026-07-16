## ADDED Requirements

### Requirement: Backend endpoint answers questions using the indexed documents
The system SHALL provide a backend endpoint that accepts a natural-language question and SHALL answer it using retrieval over the persisted document index and the MiniMax LLM.

#### Scenario: Answering a question about indexed content
- **WHEN** a user submits a question that relates to content from an indexed document
- **THEN** the endpoint returns an answer generated using retrieved content from the index

#### Scenario: No documents indexed yet
- **WHEN** a user submits a question before any document has been successfully indexed
- **THEN** the endpoint returns a clear response indicating no documents are available yet, rather than an error

### Requirement: Question-answering uses MiniMax for completions
The system SHALL use the MiniMax API (via a configured API key) to generate the answer text.

#### Scenario: Asking a question without a configured MiniMax API key
- **WHEN** a user submits a question while the backend has no valid MiniMax API key configured
- **THEN** the endpoint returns a clear error response and does not crash the backend process
