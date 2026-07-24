## MODIFIED Requirements

### Requirement: Content page provides tab navigation to the ask page
The system SHALL provide a tab bar on a workspace's pages with "Ask" and
"Content" tabs, allowing navigation between that workspace's ask page
(`/w/<slug>/ask`) and content page (`/w/<slug>/feed/files`), with the tab
for the current page visually marked as selected. The system SHALL
additionally show a "Settings" tab, linking to `/w/<slug>/settings`, only
when the current visitor's `can_edit` is `true` for that workspace (see
the `workspace-management` capability); visitors without edit access see
only the "Ask" and "Content" tabs.

#### Scenario: Navigating from content to that workspace's ask page via the tab bar
- **WHEN** a user clicks the "Ask" tab on a workspace's content page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/ask` page

#### Scenario: Content tab is selected on the content page
- **WHEN** a user is on a workspace's content page
- **THEN** the "Content" tab in the tab bar is visually marked as
  selected and the other tabs are not

#### Scenario: Editor sees a three-tab bar
- **WHEN** a visitor with edit access to a workspace views that
  workspace's ask or content page
- **THEN** the tab bar shows "Ask", "Content", and "Settings"

#### Scenario: Non-editor sees a two-tab bar
- **WHEN** a visitor without edit access to a workspace views that
  workspace's ask or content page
- **THEN** the tab bar shows only "Ask" and "Content"
