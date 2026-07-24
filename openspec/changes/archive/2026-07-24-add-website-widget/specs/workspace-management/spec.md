## MODIFIED Requirements

### Requirement: Workspace responses reveal editability and owner presence, not owner identity
The system SHALL include a computed `can_edit` boolean and a computed
`has_owner` boolean on every workspace returned from the workspace
list and workspace detail endpoints. `can_edit` SHALL reflect whether
the current request (based on its own optional bearer token, if any)
is allowed to add or remove content in that workspace. `has_owner`
SHALL reflect whether the workspace has any owner at all, computed
identically regardless of who is asking or whether they are that
owner. The system SHALL NOT include the owner's identity (user id,
email, or any other identifying field) in these responses.

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

#### Scenario: Owned workspace reports has_owner true regardless of viewer
- **WHEN** any visitor, authenticated as the owner, as a different
  user, or unauthenticated, requests the details of a workspace that
  has an owner
- **THEN** the response includes `has_owner: true`

#### Scenario: Ownerless workspace reports has_owner false regardless of viewer
- **WHEN** any visitor, authenticated or not, requests the details of a
  workspace that has no owner
- **THEN** the response includes `has_owner: false`
