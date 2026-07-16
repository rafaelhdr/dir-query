## MODIFIED Requirements

### Requirement: Home page explains the project and RAG
The system SHALL serve the home page at both `/` and `/home` (the same
content at both paths), explaining what the project is, briefly
explaining what RAG (Retrieval-Augmented Generation) is, in plain
language, and explaining that workspaces are how the project separates
groups of documents (e.g. per person or company).

#### Scenario: Visiting the home page at /
- **WHEN** a user navigates to `/`
- **THEN** the page loads successfully and displays a description of the
  project, a brief explanation of RAG, and an explanation of workspaces

#### Scenario: Visiting the home page at /home
- **WHEN** a user navigates to `/home`
- **THEN** the same home page content is displayed as at `/`

### Requirement: Home page links to the other pages
The system SHALL provide a navigation link from the home page to the
workspaces page (`/workspaces`).

#### Scenario: Navigating from home to workspaces
- **WHEN** a user clicks the "Workspaces" navigation link on the home page
- **THEN** the browser navigates to `/workspaces`
