## MODIFIED Requirements

### Requirement: A user can create a workspace
The system SHALL serve a page at `/workspaces/new` with fields for a
workspace name, an optional description, and an optional LLM key
configuration (see the `workspace-llm-key-selection` capability), and SHALL
create a new `workspaces` row on submission, deriving a URL-safe slug from
the name. If the request is authenticated (a valid bearer token is
presented), the new workspace's owner is set to that token's user;
otherwise the workspace is created with no owner.

#### Scenario: Creating a workspace while logged in
- **WHEN** an authenticated user submits the workspace creation form
  with a name
- **THEN** a new workspace is created with a slug derived from the name
  (e.g. "Company X" → `company-x`), owned by that user, and the user is
  taken to that workspace

#### Scenario: Creating a workspace while logged out
- **WHEN** an unauthenticated visitor submits the workspace creation
  form with a name
- **THEN** a new workspace is created with a slug derived from the
  name, with no owner, and the visitor is taken to that workspace

#### Scenario: Duplicate name is rejected
- **WHEN** a user creates a workspace whose derived slug already belongs
  to an existing workspace
- **THEN** the backend rejects the request with a clear error stating
  the name is already in use and does not create a new workspace

#### Scenario: Missing required field is rejected
- **WHEN** a user submits the workspace creation form without a name
- **THEN** the backend responds with a clear validation error and does
  not create a workspace

#### Scenario: Creating a workspace with a description
- **WHEN** a user submits the workspace creation form with a name and a
  description
- **THEN** a new workspace is created with that description stored
  alongside it

#### Scenario: Creating a workspace without a description
- **WHEN** a user submits the workspace creation form with a name and no
  description
- **THEN** a new workspace is created with an empty description, and
  creation is not blocked by the missing description

## ADDED Requirements

### Requirement: A workspace's description is shown on the workspaces list
The system SHALL include each workspace's description in workspace list and
detail responses, and SHALL render it below that workspace's title on the
`/workspaces` page as sanitized Markdown with line breaks preserved.

#### Scenario: Workspace with a description appears on the list
- **WHEN** a user navigates to `/workspaces` and a listed workspace has a
  non-empty description
- **THEN** that workspace's description is displayed below its title,
  rendered as sanitized Markdown

#### Scenario: Workspace without a description appears on the list
- **WHEN** a user navigates to `/workspaces` and a listed workspace has an
  empty description
- **THEN** that workspace is listed with no description content shown
