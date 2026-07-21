## ADDED Requirements

### Requirement: Uploading to an owned workspace requires the owner's session
The system SHALL restrict `POST /w/<slug>/uploads` to the workspace's
owner when that workspace has one: the request MUST carry a valid
bearer token belonging to the owning user, or the backend SHALL reject
it without persisting the file. Uploads to a workspace with no owner
SHALL remain unrestricted, as today.

#### Scenario: Owner can upload to their own workspace
- **WHEN** the user who owns a workspace uploads a valid PDF with a
  valid bearer token
- **THEN** the upload succeeds as normal

#### Scenario: Non-owner is rejected
- **WHEN** a different authenticated user, or an unauthenticated
  visitor, attempts to upload a file to a workspace owned by someone
  else
- **THEN** the backend rejects the request and does not persist the
  file

#### Scenario: Anyone can upload to an ownerless workspace
- **WHEN** any visitor, authenticated or not, uploads a valid PDF to a
  workspace that has no owner
- **THEN** the upload succeeds as normal

### Requirement: The add-content section is hidden when the visitor cannot edit
The system SHALL hide the "Add content" section on a workspace's
content page (`/w/<slug>/feed/files`) when that workspace's `can_edit`
is `false` for the current visitor, and SHALL show it when `can_edit`
is `true`.

#### Scenario: Non-owner does not see the add-content section
- **WHEN** a visitor who is not the owner views the content page of an
  owned workspace
- **THEN** the "Add content" section is not rendered

#### Scenario: Anyone sees the add-content section on an ownerless workspace
- **WHEN** any visitor views the content page of a workspace with no
  owner
- **THEN** the "Add content" section is rendered as usual
