## MODIFIED Requirements

### Requirement: Home page explains the project and RAG
The system SHALL serve the home page at `/` only, explaining what Dir
Query is (using AI to understand your own documents and ask questions
grounded in them, i.e. RAG) and briefly defining a workspace as a
separate collection of documents (e.g. per person or company), with
links to two example workspaces so a visitor can try the product
immediately; explaining that the project is open source and
self-hostable, with a link to its GitHub repository and a way to create
your own workspace; and naming the technologies the project is built on.

#### Scenario: Visiting the home page at /
- **WHEN** a user navigates to `/`
- **THEN** the page loads successfully and displays a description of the
  project with a brief definition of "workspace", two links to example
  workspaces, an explanation that the project is open source and
  self-hostable with a link to its GitHub repository, a way to create a
  new workspace, and a summary of the technologies the project uses

#### Scenario: Navigating to an example workspace from the home page
- **WHEN** a user clicks one of the home page's two example workspace
  links
- **THEN** the browser navigates to that workspace's ask page

#### Scenario: Navigating to the GitHub repository from the home page
- **WHEN** a user clicks the home page's link to the project's source
  code
- **THEN** the browser navigates to the project's GitHub repository
