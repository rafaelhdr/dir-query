## MODIFIED Requirements

### Requirement: Ask page links to the other pages
The system SHALL provide navigation from a workspace's ask page to the
home page (`/home`) and, via a tab bar shared with the workspace's
upload page, to that same workspace's upload page
(`/w/<slug>/feed/upload`), with the "Ask" tab visually marked as the
selected tab.

#### Scenario: Navigating from ask to home
- **WHEN** a user clicks the "Home" navigation link on the ask page
- **THEN** the browser navigates to `/home`

#### Scenario: Navigating from ask to that workspace's upload page via the tab bar
- **WHEN** a user clicks the "Upload" tab on a workspace's ask page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/feed/upload` page

#### Scenario: Ask tab is selected on the ask page
- **WHEN** a user is on a workspace's ask page
- **THEN** the "Ask" tab in the tab bar is visually marked as selected
  and the "Upload" tab is not

## ADDED Requirements

### Requirement: Ask page heading shows the workspace's name
The system SHALL display the workspace's name (not a generic label) as
the `<h1>` heading on a workspace's ask page, fetched from the backend
using the slug in the URL.

#### Scenario: Workspace name appears in the heading
- **WHEN** a user navigates to `/w/<slug>/ask` for a workspace named
  "Acme Corp" (slug `acme-corp`)
- **THEN** the page's `<h1>` displays "Acme Corp"

#### Scenario: Nonexistent workspace
- **WHEN** a user navigates to `/w/<slug>/ask` for a slug that does not
  correspond to any existing workspace
- **THEN** the page indicates the workspace could not be found instead
  of displaying a workspace name

### Requirement: Bare workspace URL defaults to the ask page
The system SHALL serve the ask page, with its "Ask" tab selected, when a
user navigates to a workspace's bare URL `/w/<slug>` for an existing
workspace.

#### Scenario: Opening a workspace by its bare URL
- **WHEN** a user navigates to `/w/<slug>` for a workspace that exists
- **THEN** the ask page for that workspace loads, showing that
  workspace's name in the heading and the "Ask" tab selected
