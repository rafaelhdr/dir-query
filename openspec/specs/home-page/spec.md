## Purpose

The home page (`/`) is the entry point of the application. It explains what the project is, briefly explains what RAG (Retrieval-Augmented Generation) is, discloses beta status, and links to the other pages.

## Requirements

### Requirement: Home page explains the project and RAG
The system SHALL serve a home page at `/` that explains what the project is and briefly explains what RAG (Retrieval-Augmented Generation) is, in plain language.

#### Scenario: Visiting the home page
- **WHEN** a user navigates to `/`
- **THEN** the page loads successfully and displays a description of the project and a brief explanation of RAG

### Requirement: Home page discloses beta status
The system SHALL clearly indicate on the home page that the application is a beta version, and that uploaded documents are not yet processed or searchable.

#### Scenario: Beta notice is visible
- **WHEN** a user views the home page
- **THEN** a visible notice states the application is in beta and that uploads are not yet acted upon

### Requirement: Home page links to the other pages
The system SHALL provide navigation links from the home page to the ask page (`/ask`) and the upload page (`/feed/upload`).

#### Scenario: Navigating from home to ask
- **WHEN** a user clicks the "Ask" navigation link on the home page
- **THEN** the browser navigates to `/ask`

#### Scenario: Navigating from home to upload
- **WHEN** a user clicks the "Upload" navigation link on the home page
- **THEN** the browser navigates to `/feed/upload`
