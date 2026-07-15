## Purpose

The ask page (`/ask`) is the future home of RAG-based question answering. In its current form it only provides the input UI, with no backend integration yet.

## Requirements

### Requirement: Ask page provides a question input
The system SHALL serve a page at `/ask` with a text input, positioned at the bottom of the page, where a user can type a question.

#### Scenario: Visiting the ask page
- **WHEN** a user navigates to `/ask`
- **THEN** the page loads successfully and displays a question input at the bottom of the page

### Requirement: Ask page is a non-functional placeholder
The system SHALL NOT send the question to any backend endpoint or produce an answer when the user submits the input in this change; the page exists as the future location of RAG Q&A.

#### Scenario: Submitting a question does nothing
- **WHEN** a user types a question into the input and submits it
- **THEN** no request is sent to the backend and no answer is displayed

### Requirement: Ask page links to the other pages
The system SHALL provide navigation links from the ask page to the home page (`/`) and the upload page (`/feed/upload`).

#### Scenario: Navigating from ask to home
- **WHEN** a user clicks the "Home" navigation link on the ask page
- **THEN** the browser navigates to `/`
