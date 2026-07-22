## MODIFIED Requirements

### Requirement: The content page shows every file with a manual refresh
The system SHALL display, on the content page, every file uploaded to the
current workspace with its display name, status, an "Open" control, and a
"Delete" control, with no pagination or infinite scroll. The display name
SHALL be rendered as plain text (not a link), paired with an "Edit" control
that lets the file be renamed inline. Opening a file's content SHALL be
done via a dedicated "Open" control in the actions column, positioned
before "Delete", rather than by clicking the display name. The system
SHALL NOT display the file's original filename on the content page (it is
tracked and validated server-side, but is not part of the list UI). The
system SHALL provide a refresh control above the list that reloads the
list from the backend on demand.

#### Scenario: Files list renders below the add-content section
- **WHEN** a user visits a workspace's content page and files have been
  uploaded to it
- **THEN** every uploaded file is shown with its display name as plain
  text, its status, an "Open" button, and a "Delete" button, with no
  original-filename column and no pagination controls

#### Scenario: Refresh reloads current status from the backend
- **WHEN** a user clicks the refresh control while a file's status is
  `pending`
- **THEN** the list is re-fetched from the backend, and if that file has
  since become `indexed` (or `failed`), the updated status is displayed

#### Scenario: Opening a file via the Open button
- **WHEN** a user clicks a file's "Open" button in the list
- **THEN** that file's content opens in a new browser tab

#### Scenario: Deleting a file via its Delete button
- **WHEN** a user clicks a file's "Delete" button in the list
- **THEN** the file is deleted on the backend and no longer appears in
  the list after the list next refreshes

### Requirement: Delete controls are hidden when the visitor cannot edit
The system SHALL hide each file's "Delete" button and "Edit" control on a
workspace's content page when that workspace's `can_edit` is `false` for
the current visitor, and SHALL show both when `can_edit` is `true`.
Listing files and opening a file's content via the "Open" button are
unaffected by `can_edit` and remain available to everyone.

#### Scenario: Non-owner does not see delete or edit controls
- **WHEN** a visitor who is not the owner views the file list on an
  owned workspace's content page
- **THEN** no file in the list shows a "Delete" button or an "Edit"
  control

#### Scenario: Anyone sees delete and edit controls on an ownerless workspace
- **WHEN** any visitor views the file list on a workspace with no owner
- **THEN** every file in the list shows a "Delete" button and an "Edit"
  control

#### Scenario: Non-owner can still view and open files
- **WHEN** a visitor who is not the owner views an owned workspace's
  content page
- **THEN** the file list, statuses, and "Open" buttons are still shown
  normally, even though "Delete" and "Edit" are hidden

## ADDED Requirements

### Requirement: A file's display name can be renamed inline
The system SHALL let a visitor with edit access to a workspace rename any
file's display name directly from the content page's file list, via an
"Edit" control that switches that file's name into an editable text field
pre-populated with the current name, alongside explicit "Save" and
"Cancel" controls. Pressing Enter while editing SHALL be equivalent to
activating "Save"; pressing Escape SHALL be equivalent to activating
"Cancel". On a successful save, the system SHALL persist the new display
name and refresh the file list from the backend. On a failed save, the
system SHALL keep the field in its editable state and display the failure
reason inline near the field, rather than discarding the in-progress edit
or using a native browser dialog.

#### Scenario: Renaming a file successfully
- **WHEN** a visitor with edit access clicks "Edit" on a file, changes its
  name to a value not used by any other file in the workspace, and saves
- **THEN** the file's display name is updated on the backend and the list
  shows the new name after it refreshes

#### Scenario: Cancelling an in-progress rename
- **WHEN** a visitor clicks "Edit", changes the text, then activates
  "Cancel" (or presses Escape) before saving
- **THEN** no request is sent and the file's display name in the list is
  unchanged

#### Scenario: Renaming to a name already used in the workspace is rejected
- **WHEN** a visitor attempts to save a new display name that matches
  another file's display name in the same workspace
- **THEN** the rename is rejected, the field stays open for editing, and
  an inline message explains the name is already in use

#### Scenario: Renaming to a blank name is rejected
- **WHEN** a visitor attempts to save an empty or whitespace-only display
  name
- **THEN** the rename is rejected, the field stays open for editing, and
  an inline message explains the name cannot be blank

#### Scenario: Renaming a file to its own current name succeeds
- **WHEN** a visitor saves a rename with the field unchanged from the
  file's existing display name
- **THEN** the rename succeeds (the file is not treated as conflicting
  with itself)

#### Scenario: A visitor without edit access cannot rename a file
- **WHEN** a request to rename a file is made without edit access to its
  workspace
- **THEN** the backend rejects the request and the file's display name is
  unchanged
