## Purpose

The ask page (`/w/<slug>/ask`) is where a user asks questions about a
workspace's uploaded documents. It submits the question to that
workspace's backend question-answering endpoint and displays the
returned answer.

## Requirements

### Requirement: Ask page provides a question input
The system SHALL serve a page at `/w/<slug>/ask` for an existing workspace
identified by `<slug>`, with a text input, positioned at the bottom of the
page, where a user can type a question for that workspace.

#### Scenario: Visiting the ask page for an existing workspace
- **WHEN** a user navigates to `/w/<slug>/ask` for a workspace that exists
- **THEN** the page loads successfully and displays a question input at
  the bottom of the page

### Requirement: Ask page submits questions to the backend and displays the answer
The system SHALL submit the question entered on a workspace's ask page to
that workspace's backend question-answering endpoint and SHALL display
the returned answer on the page.

#### Scenario: Submitting a question shows an answer
- **WHEN** a user types a question into the input on a workspace's ask
  page and submits it
- **THEN** the question is sent to the backend for that workspace and the
  returned answer is displayed on the page

#### Scenario: Backend error is shown to the user
- **WHEN** the backend returns an error in response to a submitted
  question
- **THEN** the ask page displays a clear error message instead of an
  answer

### Requirement: Ask page links to the other pages
The system SHALL provide navigation links from a workspace's ask page to
the home page (`/home`) and that same workspace's upload page
(`/w/<slug>/feed/upload`).

#### Scenario: Navigating from ask to home
- **WHEN** a user clicks the "Home" navigation link on the ask page
- **THEN** the browser navigates to `/home`

#### Scenario: Navigating from ask to that workspace's upload page
- **WHEN** a user clicks the "Upload" navigation link on a workspace's
  ask page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/feed/upload` page
</content>
</invoke>
