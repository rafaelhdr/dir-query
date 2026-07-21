## MODIFIED Requirements

### Requirement: Uploading to an owned workspace requires the owner's session
The system SHALL restrict `POST /w/<slug>/files` to the workspace's
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
