## ADDED Requirements

### Requirement: A user with edit access can edit an existing workspace's name and description
The system SHALL serve a page at `/w/<slug>/settings` for an existing
workspace, showing editable fields for the workspace's name and
description (in addition to LLM key configuration, covered by the
`workspace-llm-key-selection` capability), and SHALL provide
`PATCH /workspaces/{slug}` to persist changes. This endpoint is a
full-submission endpoint: the request MUST include the workspace's
complete current field set (name, description, and LLM key fields), not
a partial diff. The endpoint SHALL be restricted the same way editing a
workspace's content already is: allowed when the requester's `can_edit`
for that workspace is `true`, rejected otherwise, with nothing changed.

#### Scenario: Editor saves a description change
- **WHEN** a visitor with edit access to a workspace submits the settings
  form with an unchanged name and a new description
- **THEN** the workspace's description is updated and the new value is
  reflected the next time the workspace is fetched

#### Scenario: Non-editor cannot save changes
- **WHEN** a request to `PATCH /workspaces/{slug}` is made without edit
  access to that workspace
- **THEN** the backend rejects the request and none of the workspace's
  fields are changed

#### Scenario: Resubmitting unchanged values succeeds
- **WHEN** an editor submits the settings form with every field identical
  to the workspace's current values
- **THEN** the save succeeds and is not treated as a conflict with the
  workspace's own existing values

### Requirement: Editing a workspace's name recomputes its slug
The system SHALL derive a new slug from an edited name using the same
slugify logic used at workspace creation, and SHALL update the
workspace's slug accordingly. If the recomputed slug already belongs to
a different existing workspace, the system SHALL reject the request with
a clear conflict error and SHALL NOT change the workspace's name, slug,
or any other field. The system SHALL NOT retain any redirect or alias
from a workspace's previous slug to its new one — a URL built from the
old slug SHALL simply stop resolving once the slug changes.

#### Scenario: Renaming a workspace changes its slug
- **WHEN** an editor changes a workspace's name from "Acme Corp" to
  "Acme Corporation" and saves
- **THEN** the workspace's slug is recomputed from the new name (e.g.
  `acme-corp` → `acme-corporation`) and the workspace is reachable at
  the new slug

#### Scenario: Renaming to a name whose slug collides with another workspace
- **WHEN** an editor edits a workspace's name to a value whose derived
  slug already belongs to a different existing workspace
- **THEN** the backend rejects the request with a clear conflict error
  and the workspace's name, slug, and other fields remain unchanged

#### Scenario: Old slug no longer resolves after a rename
- **WHEN** a workspace's name (and therefore slug) has been successfully
  changed
- **THEN** a request using the workspace's previous slug no longer
  resolves to that workspace

### Requirement: The frontend navigates to a workspace's new URL after a rename
The system SHALL, on the settings page, navigate the browser to the
workspace's new `/w/<new-slug>/settings` URL immediately after a
successful save that changed the workspace's slug, rather than remaining
on the now-stale URL.

#### Scenario: Saving a name change navigates to the new URL
- **WHEN** an editor successfully saves a name change that changes the
  workspace's slug from `acme-corp` to `acme-corporation`
- **THEN** the browser navigates to `/w/acme-corporation/settings`

#### Scenario: Saving without a name change does not navigate
- **WHEN** an editor successfully saves changes that leave the workspace's
  name (and therefore slug) unchanged
- **THEN** the browser remains on the current URL

### Requirement: Editing the name warns that the workspace's current URL will stop working
The system SHALL display a warning on the settings page when the name
field is edited to a value whose derived slug differs from the
workspace's current slug, stating that saving this change will make the
workspace's current URL stop working, and that anything referencing that
URL (for example, a link in a blog post, or — in the future — an
embedded widget) will need to be updated to the new URL once it is
known. This warning is informational only and SHALL NOT block saving.

#### Scenario: Warning appears when the edited name would change the slug
- **WHEN** an editor on the settings page changes the name field to a
  value whose derived slug differs from the workspace's current slug
- **THEN** a warning is shown explaining that the current URL will stop
  working and that any existing references to it will need updating

#### Scenario: No warning when the edited name keeps the same slug
- **WHEN** an editor edits the name field but the derived slug is
  unchanged from the workspace's current slug (e.g. only capitalization
  or punctuation not reflected in the slug changed)
- **THEN** no URL-change warning is shown

#### Scenario: The warning does not block saving
- **WHEN** an editor sees the URL-change warning and proceeds to save
- **THEN** the save proceeds normally, subject only to the other
  validation rules (e.g. slug collision)

### Requirement: The settings page is reachable only by editors
The system SHALL add a "Settings" tab to the existing tab bar on a
workspace's pages, visible only when that workspace's `can_edit` is
`true` for the current visitor (see `document-upload`'s tab bar
requirement for the full tab set). The system SHALL redirect a visitor
without edit access who navigates directly to `/w/<slug>/settings` to
that workspace's content page (`/w/<slug>/feed/files`) instead of
rendering the settings form.

#### Scenario: Editor sees and can use the Settings tab
- **WHEN** a visitor with edit access to a workspace views any of that
  workspace's pages
- **THEN** a "Settings" tab is shown in the tab bar, linking to
  `/w/<slug>/settings`

#### Scenario: Non-editor does not see the Settings tab
- **WHEN** a visitor without edit access to a workspace views any of that
  workspace's pages
- **THEN** no "Settings" tab is shown in the tab bar

#### Scenario: Non-editor loading the settings URL directly is redirected
- **WHEN** a visitor without edit access to a workspace navigates directly
  to `/w/<slug>/settings`
- **THEN** they are redirected to `/w/<slug>/feed/files` instead of seeing
  the settings form
