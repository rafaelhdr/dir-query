## Purpose

The ask page (`/ask`) is where a user asks questions about their uploaded documents. It submits the question to the backend question-answering endpoint and displays the returned answer.

## Requirements

### Requirement: Ask page provides a question input
The system SHALL serve a page at `/ask` with a text input, positioned at the bottom of the page, where a user can type a question.

#### Scenario: Visiting the ask page
- **WHEN** a user navigates to `/ask`
- **THEN** the page loads successfully and displays a question input at the bottom of the page

### Requirement: Ask page submits questions to the backend and displays the answer
The system SHALL submit the question entered on the ask page to the backend question-answering endpoint and SHALL display the returned answer on the page.

#### Scenario: Submitting a question shows an answer
- **WHEN** a user types a question into the input and submits it
- **THEN** the question is sent to the backend and the returned answer is displayed on the page

#### Scenario: Backend error is shown to the user
- **WHEN** the backend returns an error in response to a submitted question
- **THEN** the ask page displays a clear error message instead of an answer

### Requirement: Ask page links to the other pages
The system SHALL provide navigation links from the ask page to the home page (`/`) and the upload page (`/feed/upload`).

#### Scenario: Navigating from ask to home
- **WHEN** a user clicks the "Home" navigation link on the ask page
- **THEN** the browser navigates to `/`
