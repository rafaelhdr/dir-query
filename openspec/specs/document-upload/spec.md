## Purpose

The document-upload capability lets a user push PDF documents to the
server, scoped to a workspace, from that workspace's upload page
(`/w/<slug>/feed/upload`). It is upload-only in its current form: no
parsing, indexing, or CRUD operations exist yet.

## Requirements

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

### Requirement: Only PDF files are accepted
The system SHALL accept only PDF files for upload and SHALL reject any other file type with a clear error, without storing the rejected file.

#### Scenario: Rejecting a non-PDF file
- **WHEN** a user attempts to upload a file that is not a PDF (by extension and declared content type)
- **THEN** the backend responds with an error indicating only PDF files are supported and does not persist the file

#### Scenario: Accepting a PDF file
- **WHEN** a user uploads a file with a `.pdf` extension and `application/pdf` content type
- **THEN** the backend accepts and persists the file

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

### Requirement: Upload is write-only, with no CRUD operations
The system SHALL provide no endpoints or UI to list, download, update, or delete previously uploaded files in this change; uploading is the only supported operation.

#### Scenario: No listing capability exists
- **WHEN** a user looks for a way to view previously uploaded files
- **THEN** no such listing page or endpoint is available

### Requirement: Oversized uploads are rejected
The system SHALL reject uploads larger than a configured maximum size with a clear error, without persisting the file.

#### Scenario: File exceeds size limit
- **WHEN** a user attempts to upload a PDF larger than the configured maximum upload size
- **THEN** the backend rejects the upload with an error and does not persist the file
</content>
