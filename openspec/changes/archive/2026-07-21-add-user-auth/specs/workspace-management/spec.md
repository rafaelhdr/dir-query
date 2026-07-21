## MODIFIED Requirements

### Requirement: A user can create a workspace
The system SHALL serve a page at `/workspaces/new` with a field for a
workspace name only, and SHALL create a new `workspaces` row on
submission, deriving a URL-safe slug from the name. If the request is
authenticated (a valid bearer token is presented), the new workspace's
owner is set to that token's user; otherwise the workspace is created
with no owner.

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

## REMOVED Requirements

### Requirement: Workspace owner email is not exposed publicly
**Reason**: `workspaces.owner_email` is removed. Ownership is now
tracked via a link to a `users` account, and API responses expose only
whether the current requester can edit the workspace, never who owns
it — see the new "Workspace responses reveal editability, not owner
identity" requirement.
**Migration**: No data migration; `owner_email` is dropped from the
`workspaces` table. Any external consumer that relied on this field
being absent (it always was) is unaffected.

### Requirement: Workspace passwords are stored hashed
**Reason**: Per-workspace passwords are removed entirely — they were
never verified by any endpoint. Access to add/remove workspace content
is now controlled by user-account ownership (see the `user-auth`
capability), not a workspace-level password.
**Migration**: `workspaces.password` is dropped from the table.
Existing hashed values are discarded; nothing reads or verifies them
today.

## ADDED Requirements

### Requirement: Workspace responses reveal editability, not owner identity
The system SHALL include a computed `can_edit` boolean on every
workspace returned from the workspace list and workspace detail
endpoints, reflecting whether the current request (based on its own
optional bearer token, if any) is allowed to add or remove content in
that workspace. The system SHALL NOT include the owner's identity (user
id, email, or any other identifying field) in these responses.

#### Scenario: Owner sees can_edit true
- **WHEN** the user who owns a workspace requests that workspace's
  details with a valid bearer token
- **THEN** the response includes `can_edit: true`

#### Scenario: Non-owner sees can_edit false
- **WHEN** a different authenticated user (not the owner), or an
  unauthenticated visitor, requests an owned workspace's details
- **THEN** the response includes `can_edit: false`

#### Scenario: Anyone sees can_edit true for an ownerless workspace
- **WHEN** any visitor, authenticated or not, requests the details of a
  workspace that has no owner
- **THEN** the response includes `can_edit: true`

#### Scenario: Owner identity is never present in the response
- **WHEN** a workspace is created, listed, or fetched by slug, by
  anyone
- **THEN** the response body does not include the owning user's id,
  email, or any other identifying field
