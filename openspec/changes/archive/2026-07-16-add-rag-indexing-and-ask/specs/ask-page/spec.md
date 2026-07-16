## ADDED Requirements

### Requirement: Ask page submits questions to the backend and displays the answer
The system SHALL submit the question entered on the ask page to the backend question-answering endpoint and SHALL display the returned answer on the page.

#### Scenario: Submitting a question shows an answer
- **WHEN** a user types a question into the input and submits it
- **THEN** the question is sent to the backend and the returned answer is displayed on the page

#### Scenario: Backend error is shown to the user
- **WHEN** the backend returns an error in response to a submitted question
- **THEN** the ask page displays a clear error message instead of an answer

## REMOVED Requirements

### Requirement: Ask page is a non-functional placeholder
**Reason**: The `document-indexing` and `question-answering` capabilities now provide a working RAG backend, so the ask page is wired up to it instead of remaining a placeholder.
**Migration**: No user-facing migration; existing links to `/ask` continue to work, but submitting a question now produces a real answer instead of doing nothing.
