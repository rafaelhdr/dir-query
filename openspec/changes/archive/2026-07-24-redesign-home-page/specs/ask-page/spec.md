## MODIFIED Requirements

### Requirement: Ask page links to the other pages
The system SHALL provide navigation from a workspace's ask page to the
home page (`/`) and, via a tab bar shared with the workspace's upload
page, to that same workspace's upload page (`/w/<slug>/feed/upload`),
with the "Ask" tab visually marked as the selected tab.

#### Scenario: Navigating from ask to home
- **WHEN** a user clicks the "Home" navigation link on the ask page
- **THEN** the browser navigates to `/`

#### Scenario: Navigating from ask to that workspace's upload page via the tab bar
- **WHEN** a user clicks the "Upload" tab on a workspace's ask page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/feed/upload` page

#### Scenario: Ask tab is selected on the ask page
- **WHEN** a user is on a workspace's ask page
- **THEN** the "Ask" tab in the tab bar is visually marked as selected
  and the "Upload" tab is not
