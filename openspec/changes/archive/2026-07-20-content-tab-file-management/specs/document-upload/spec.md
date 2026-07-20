## ADDED Requirements

### Requirement: Add-content section is collapsible and prefills the display name
The system SHALL present the upload form on the content page inside a
collapsible "Add content" section that starts collapsed. When the user
selects a local file, the system SHALL prefill an editable display-name
field with that file's filename, which the user may change before
submitting.

#### Scenario: Add-content section starts collapsed
- **WHEN** a user visits a workspace's content page
- **THEN** the "Add content" section is collapsed by default

#### Scenario: Selecting a file prefills the name field
- **WHEN** a user expands the "Add content" section and selects a local
  file named `report.pdf`
- **THEN** the display-name field is prefilled with `report.pdf`, editable
  before submission

#### Scenario: User overrides the prefilled name
- **WHEN** a user selects a file and edits the prefilled display-name
  field before submitting
- **THEN** the edited name, not the original filename, is submitted as
  the display name

### Requirement: Duplicate display names are rejected within a workspace
The system SHALL reject an upload whose display name already belongs to
another file in the same workspace, with a clear error, without
persisting the file, and without clearing the user's already-entered form
fields.

#### Scenario: Uploading a name that already exists in the workspace
- **WHEN** a user submits an upload whose display name matches an existing
  file's display name in the same workspace
- **THEN** the backend rejects the upload with a clear conflict error and
  does not persist the file

#### Scenario: Same display name is allowed across different workspaces
- **WHEN** two different workspaces each have a file uploaded with the
  same display name
- **THEN** both uploads succeed, since the uniqueness check is scoped per
  workspace

#### Scenario: Successful upload clears the form and refreshes the list
- **WHEN** a user submits an upload with a unique display name and it
  succeeds
- **THEN** the add-content section's fields are cleared and the file list
  is refreshed to include the new file

### Requirement: Duplicate original filenames are rejected within a workspace
The system SHALL track the uploaded file's own filename (its "original
filename") separately from the user-editable display name, and SHALL
reject an upload whose original filename already belongs to another file
in the same workspace, with a clear error, without persisting the file —
independently of whether the display name is unique.

#### Scenario: Uploading a file whose original filename already exists in the workspace
- **WHEN** a user uploads a local file named `report.pdf`, under any
  display name, to a workspace that already has a file whose original
  filename is `report.pdf`
- **THEN** the backend rejects the upload with a clear conflict error
  naming the conflicting filename and does not persist the file

#### Scenario: Same original filename is allowed across different workspaces
- **WHEN** two different workspaces each have a file uploaded from a local
  file named `report.pdf`
- **THEN** both uploads succeed, since the uniqueness check is scoped per
  workspace

#### Scenario: Different original filenames under the same display name are still rejected on display-name grounds
- **WHEN** a user uploads a file whose original filename is unique in the
  workspace, but whose chosen display name matches an existing file's
  display name
- **THEN** the backend still rejects the upload, since display name and
  original filename are each independently unique

## MODIFIED Requirements

### Requirement: Upload page lets the user push a PDF to the server
The system SHALL serve a page at `/w/<slug>/feed/files` for an existing
workspace identified by `<slug>` with a collapsible "Add content" section
containing a file picker, an editable display-name field, and submit
control that lets the user select a local file and upload it to the
server for that workspace under a chosen display name.

#### Scenario: Visiting the content page for an existing workspace
- **WHEN** a user navigates to `/w/<slug>/feed/files` for a workspace
  that exists
- **THEN** the page loads successfully and displays the "Add content"
  section and the file list

#### Scenario: Successful upload
- **WHEN** a user selects a valid PDF file, confirms or edits its
  prefilled display name, and submits the upload form on a workspace's
  content page
- **THEN** the file is sent to the backend for that workspace under that
  display name and the file list shows it

### Requirement: Uploaded files are persisted to server-side storage
The system SHALL store accepted PDF uploads under a server-side directory
scoped to the owning workspace, SHALL record a corresponding row in the
`files` table (`workspace_id`, `filename`, `display_name` set from the
user-provided display name, `original_filename` set from the uploaded
file's own filename, `status` starting as `pending`), and SHALL NOT parse,
index, or otherwise process the file contents as part of accepting the
upload (parsing and indexing are covered by the document-indexing
capability).

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
  display name
- **THEN** both files are stored and tracked independently, scoped to
  their own workspace

### Requirement: Content page heading shows the workspace's name
The system SHALL display the workspace's name (not a generic label) as
the `<h1>` heading on a workspace's content page, fetched from the
backend using the slug in the URL.

#### Scenario: Workspace name appears in the heading
- **WHEN** a user navigates to `/w/<slug>/feed/files` for a workspace
  named "Acme Corp" (slug `acme-corp`)
- **THEN** the page's `<h1>` displays "Acme Corp"

#### Scenario: Nonexistent workspace
- **WHEN** a user navigates to `/w/<slug>/feed/files` for a slug that
  does not correspond to any existing workspace
- **THEN** the page indicates the workspace could not be found instead
  of displaying a workspace name

### Requirement: Content page provides tab navigation to the ask page
The system SHALL provide a tab bar on a workspace's content page with
"Ask" and "Content" tabs, allowing navigation to that same workspace's ask
page (`/w/<slug>/ask`), with the "Content" tab visually marked as the
selected tab.

#### Scenario: Navigating from content to that workspace's ask page via the tab bar
- **WHEN** a user clicks the "Ask" tab on a workspace's content page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/ask` page

#### Scenario: Content tab is selected on the content page
- **WHEN** a user is on a workspace's content page
- **THEN** the "Content" tab in the tab bar is visually marked as
  selected and the "Ask" tab is not

## REMOVED Requirements

### Requirement: Upload is write-only, with no CRUD operations
**Reason**: Superseded by the new `document-management` capability, which
adds listing, opening, and deleting previously uploaded files.
**Migration**: No migration needed; existing uploaded files are usable
immediately with the new list/open/delete endpoints and UI once this
change ships.

#### Scenario: No listing capability exists
- **WHEN** a user looks for a way to view previously uploaded files
- **THEN** no such listing page or endpoint is available
