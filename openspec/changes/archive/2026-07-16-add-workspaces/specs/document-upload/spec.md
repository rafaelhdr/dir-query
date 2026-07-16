## MODIFIED Requirements

### Requirement: Upload page lets the user push a PDF to the server
The system SHALL serve a page at `/w/<slug>/feed/upload` for an existing
workspace identified by `<slug>` with a file picker and submit control
that lets the user select a local file and upload it to the server for
that workspace.

#### Scenario: Visiting the upload page for an existing workspace
- **WHEN** a user navigates to `/w/<slug>/feed/upload` for a workspace
  that exists
- **THEN** the page loads successfully and displays a file upload control

#### Scenario: Successful upload
- **WHEN** a user selects a valid PDF file and submits the upload form on
  a workspace's upload page
- **THEN** the file is sent to the backend for that workspace and the
  page shows a success confirmation

### Requirement: Uploaded files are persisted to server-side storage
The system SHALL store accepted PDF uploads under a server-side directory
scoped to the owning workspace, SHALL record a corresponding row in the
`files` table (`workspace_id`, `filename`, `original_name`, `status`
starting as `pending`), and SHALL NOT parse, index, or otherwise process
the file contents as part of accepting the upload (parsing and indexing
are covered by the document-indexing capability).

#### Scenario: Uploaded file persists after restart
- **WHEN** a PDF file has been successfully uploaded to a workspace and
  the backend service is restarted
- **THEN** the previously uploaded file still exists in that workspace's
  server-side storage and its `files` row is still present

#### Scenario: Upload to a nonexistent workspace is rejected
- **WHEN** a user attempts to upload a file to a slug that does not
  correspond to any existing workspace
- **THEN** the backend responds with a 404 error and does not persist the
  file

#### Scenario: Files from different workspaces do not collide
- **WHEN** two different workspaces each upload a file with the same
  original filename
- **THEN** both files are stored and tracked independently, scoped to
  their own workspace
