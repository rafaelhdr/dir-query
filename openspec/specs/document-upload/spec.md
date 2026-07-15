## Purpose

The document-upload capability lets a user push PDF documents to the server from the upload page (`/feed/upload`). It is upload-only in its current form: no parsing, indexing, or CRUD operations exist yet.

## Requirements

### Requirement: Upload page lets the user push a PDF to the server
The system SHALL serve a page at `/feed/upload` with a file picker and submit control that lets the user select a local file and upload it to the server.

#### Scenario: Visiting the upload page
- **WHEN** a user navigates to `/feed/upload`
- **THEN** the page loads successfully and displays a file upload control

#### Scenario: Successful upload
- **WHEN** a user selects a valid PDF file and submits the upload form
- **THEN** the file is sent to the backend and the page shows a success confirmation

### Requirement: Only PDF files are accepted
The system SHALL accept only PDF files for upload and SHALL reject any other file type with a clear error, without storing the rejected file.

#### Scenario: Rejecting a non-PDF file
- **WHEN** a user attempts to upload a file that is not a PDF (by extension and declared content type)
- **THEN** the backend responds with an error indicating only PDF files are supported and does not persist the file

#### Scenario: Accepting a PDF file
- **WHEN** a user uploads a file with a `.pdf` extension and `application/pdf` content type
- **THEN** the backend accepts and persists the file

### Requirement: Uploaded files are persisted to server-side storage
The system SHALL store accepted PDF uploads in a server-side directory that persists across container restarts, and SHALL NOT parse, index, or otherwise process the file contents in this change.

#### Scenario: Uploaded file persists after restart
- **WHEN** a PDF file has been successfully uploaded and the backend service is restarted
- **THEN** the previously uploaded file still exists in server-side storage

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
