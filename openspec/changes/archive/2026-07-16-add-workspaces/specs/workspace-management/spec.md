## ADDED Requirements

### Requirement: A user can create a workspace
The system SHALL serve a page at `/workspaces/new` with fields for a
workspace name, owner email, and password, and SHALL create a new
`workspaces` row on submission, deriving a URL-safe slug from the name.

#### Scenario: Creating a workspace
- **WHEN** a user submits the workspace creation form with a name, owner
  email, and password
- **THEN** a new workspace is created with a slug derived from the name
  (e.g. "Company X" → `company-x`), and the user is taken to that
  workspace

#### Scenario: Duplicate name is rejected
- **WHEN** a user creates a workspace whose derived slug already belongs to
  an existing workspace
- **THEN** the backend rejects the request with a clear error stating the
  name is already in use and does not create a new workspace

#### Scenario: Missing required field is rejected
- **WHEN** a user submits the workspace creation form without a name,
  owner email, or password
- **THEN** the backend responds with a clear validation error and does not
  create a workspace

### Requirement: Workspace owner email is not exposed publicly
The system SHALL retain a workspace's `owner_email` for internal/
administrative contact purposes only (e.g. an admin reaching out about
that workspace) and SHALL NOT include it in any public API response —
not on workspace creation, not when listing workspaces, and not when
fetching a workspace by slug.

#### Scenario: Owner email is absent from API responses
- **WHEN** a workspace is created, listed, or fetched by slug
- **THEN** the response body does not include an `owner_email` field

### Requirement: Workspace passwords are stored hashed
The system SHALL store the workspace's password only in hashed form,
using a salted hash, and SHALL NOT store or log the plaintext password
after the creation request completes.

#### Scenario: Password is not recoverable in plaintext
- **WHEN** a workspace has been created
- **THEN** the `workspaces.password` column contains a salted hash, not
  the plaintext password entered on the form

### Requirement: A user can browse existing workspaces
The system SHALL serve a page at `/workspaces` listing existing
workspaces by name, most recently created first, each linking to that
workspace, and linking to `/workspaces/new` to create another.

#### Scenario: Listing existing workspaces
- **WHEN** a user navigates to `/workspaces`
- **THEN** the page loads successfully and displays every existing
  workspace's name with a link into that workspace, ordered from most
  to least recently created

#### Scenario: No workspaces exist yet
- **WHEN** a user navigates to `/workspaces` before any workspace has been
  created
- **THEN** the page loads successfully and indicates there are no
  workspaces yet, with a link to create one
