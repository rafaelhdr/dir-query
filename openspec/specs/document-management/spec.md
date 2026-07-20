## Purpose

The document-management capability lets a user view, open, and delete
files previously uploaded to a workspace. It complements the
document-upload capability (which covers pushing new files to the
server) by providing the read/delete side of file CRUD: listing files
with their status, opening a file's content directly via URL, and
deleting a file along with its indexed chunks and stored content.

## Requirements

### Requirement: Workspace files can be listed
The system SHALL provide an endpoint that returns every file previously
uploaded to a workspace, including its id, display name, original
filename, status, and a URL that resolves directly to that file's content,
wrapped in a `data` array envelope so the response shape can later gain
pagination fields (e.g. `next`, `total`) without changing what `data`
means.

#### Scenario: Listing files in a workspace with uploads
- **WHEN** a client requests the file list for a workspace that has one
  or more uploaded files
- **THEN** the response body is a JSON object with a `data` array
  containing one entry per file, each including its id, display name,
  original filename, status, and a URL for that file's content

#### Scenario: Listing files in a workspace with no uploads
- **WHEN** a client requests the file list for a workspace that has no
  uploaded files
- **THEN** the response body is a JSON object with an empty `data` array

#### Scenario: Listing files for a nonexistent workspace
- **WHEN** a client requests the file list for a slug that does not
  correspond to any existing workspace
- **THEN** the backend responds with a 404 error

### Requirement: Each listed file includes a URL for opening it directly
The system SHALL include, in each file list entry, a URL that resolves
directly to that file's stored PDF content without requiring a request to
any file-specific backend API endpoint, so the frontend's "Open" control
can use it directly as a link target. The system SHALL NOT require the
file's bytes to pass through the backend API to be opened.

#### Scenario: A listed file's URL serves the PDF directly
- **WHEN** a client fetches the file list for a workspace with an
  uploaded file and requests the URL given in that file's list entry
- **THEN** the response is that file's PDF content with a content type a
  browser renders inline rather than downloading

#### Scenario: A deleted file's URL no longer resolves
- **WHEN** a file has been deleted and a client requests the URL that was
  previously in its list entry
- **THEN** the request no longer resolves to file content

### Requirement: A workspace file can be deleted, cascading to its chunks
The system SHALL provide an endpoint that deletes a previously uploaded
file: removing its row from the `files` table (cascading to delete its
`chunks` rows), and removing its underlying file from server-side
storage.

#### Scenario: Deleting an existing file
- **WHEN** a client deletes a workspace file by its id
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

### Requirement: The content page shows every file with a manual refresh
The system SHALL display, on the content page, every file uploaded to the
current workspace with its display name, status, and a "Delete" control,
with no pagination or infinite scroll. The display name SHALL itself be
the control that opens the file (rendered as a link with an icon
indicating it opens in a new tab), rather than a separate "Open" column.
The system SHALL NOT display the file's original filename on the content
page (it is tracked and validated server-side, but is not part of the
list UI). The system SHALL provide a refresh control above the list that
reloads the list from the backend on demand.

#### Scenario: Files list renders below the add-content section
- **WHEN** a user visits a workspace's content page and files have been
  uploaded to it
- **THEN** every uploaded file is shown with its display name (as a
  clickable, new-tab-indicating link), status, and a "Delete" button, with
  no original-filename column and no pagination controls

#### Scenario: Refresh reloads current status from the backend
- **WHEN** a user clicks the refresh control while a file's status is
  `pending`
- **THEN** the list is re-fetched from the backend, and if that file has
  since become `indexed` (or `failed`), the updated status is displayed

#### Scenario: Opening a file via its display name
- **WHEN** a user clicks a file's display name in the list
- **THEN** that file's content opens in a new browser tab

#### Scenario: Deleting a file via its Delete button
- **WHEN** a user clicks a file's "Delete" button in the list
- **THEN** the file is deleted on the backend and no longer appears in
  the list after the list next refreshes
</content>
