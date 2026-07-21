## MODIFIED Requirements

### Requirement: A workspace file can be deleted, cascading to its chunks
The system SHALL provide an endpoint that deletes a previously uploaded
file: removing its row from the `files` table (cascading to delete its
`chunks` rows), and removing its underlying file from server-side
storage. When the file's workspace has an owner, the system SHALL
restrict this endpoint to that owner: the request MUST carry a valid
bearer token belonging to the owning user, or the backend SHALL reject
it and delete nothing. Deletes on a workspace with no owner SHALL
remain unrestricted, as today.

#### Scenario: Deleting an existing file
- **WHEN** a client with permission to edit the file's workspace
  deletes that file by its id
- **THEN** the file's `files` row no longer exists, its `chunks` rows no
  longer exist, and its underlying file is no longer present in
  server-side storage

#### Scenario: Deleting a file that does not exist
- **WHEN** a client attempts to delete a file id that does not exist (or
  does not belong to the given workspace)
- **THEN** the backend responds with a 404 error and no other file is
  affected

#### Scenario: Deleting one file does not affect others
- **WHEN** a workspace has multiple uploaded files and one is deleted
- **THEN** the remaining files' rows, chunks, and stored content are
  unaffected

#### Scenario: Non-owner cannot delete a file from an owned workspace
- **WHEN** a different authenticated user, or an unauthenticated
  visitor, attempts to delete a file belonging to a workspace owned by
  someone else
- **THEN** the backend rejects the request and the file is not deleted

#### Scenario: Anyone can delete a file from an ownerless workspace
- **WHEN** any visitor, authenticated or not, deletes a file belonging
  to a workspace that has no owner
- **THEN** the file is deleted as normal

## ADDED Requirements

### Requirement: Delete controls are hidden when the visitor cannot edit
The system SHALL hide each file's "Delete" button on a workspace's
content page when that workspace's `can_edit` is `false` for the
current visitor, and SHALL show it when `can_edit` is `true`. Listing
files and opening a file's content are unaffected by `can_edit` and
remain available to everyone.

#### Scenario: Non-owner does not see delete buttons
- **WHEN** a visitor who is not the owner views the file list on an
  owned workspace's content page
- **THEN** no file in the list shows a "Delete" button

#### Scenario: Anyone sees delete buttons on an ownerless workspace
- **WHEN** any visitor views the file list on a workspace with no owner
- **THEN** every file in the list shows a "Delete" button

#### Scenario: Non-owner can still view and open files
- **WHEN** a visitor who is not the owner views an owned workspace's
  content page
- **THEN** the file list, statuses, and "open in new tab" links are
  still shown normally
