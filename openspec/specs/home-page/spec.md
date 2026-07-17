## Purpose

The home page (served at both `/` and `/home`) is the entry point of the
application. It explains what the project is, briefly explains what RAG
(Retrieval-Augmented Generation) is, explains workspaces as the way the
project separates groups of documents, discloses beta status, and links
to the other pages.

## Requirements

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

### Requirement: Home page discloses beta status
The system SHALL clearly indicate, via a badge in the site header shown on
every page, that the application is a beta version, and that uploaded
documents are not yet processed or searchable.

#### Scenario: Beta notice is visible
- **WHEN** a user views any page of the application
- **THEN** the site header displays a visible badge stating the
  application is in beta, and uploads are not yet processed or searchable

### Requirement: Home page links to the other pages
The system SHALL provide a navigation link from the home page to the
workspaces page (`/workspaces`).

#### Scenario: Navigating from home to workspaces
- **WHEN** a user clicks the "Workspaces" navigation link on the home page
- **THEN** the browser navigates to `/workspaces`
</content>
