## ADDED Requirements

### Requirement: Upload page heading shows the workspace's name
The system SHALL display the workspace's name (not a generic label) as
the `<h1>` heading on a workspace's upload page, fetched from the
backend using the slug in the URL.

#### Scenario: Workspace name appears in the heading
- **WHEN** a user navigates to `/w/<slug>/feed/upload` for a workspace
  named "Acme Corp" (slug `acme-corp`)
- **THEN** the page's `<h1>` displays "Acme Corp"

#### Scenario: Nonexistent workspace
- **WHEN** a user navigates to `/w/<slug>/feed/upload` for a slug that
  does not correspond to any existing workspace
- **THEN** the page indicates the workspace could not be found instead
  of displaying a workspace name

### Requirement: Upload page provides tab navigation to the ask page
The system SHALL provide a tab bar on a workspace's upload page with
"Ask" and "Upload" tabs, allowing navigation to that same workspace's
ask page (`/w/<slug>/ask`), with the "Upload" tab visually marked as
the selected tab.

#### Scenario: Navigating from upload to that workspace's ask page via the tab bar
- **WHEN** a user clicks the "Ask" tab on a workspace's upload page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/ask` page

#### Scenario: Upload tab is selected on the upload page
- **WHEN** a user is on a workspace's upload page
- **THEN** the "Upload" tab in the tab bar is visually marked as
  selected and the "Ask" tab is not
