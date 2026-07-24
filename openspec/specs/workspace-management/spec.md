## Purpose

The workspace-management capability lets users create and browse
workspaces — the unit of isolation that separates groups of documents
(e.g. per person or company). A workspace has a name and a URL-safe
slug derived from that name. Ownership is optional: a workspace
created by a logged-in user (see the `user-auth` capability) is owned
by that user and only they can edit it; a workspace created without
logging in has no owner and stays fully public and editable by anyone.

## Requirements

### Requirement: A user can create a workspace
The system SHALL serve a page at `/workspaces/new` with fields for a
workspace name, an optional description, and an optional LLM key
configuration (see the `workspace-llm-key-selection` capability), and SHALL
create a new `workspaces` row on submission, deriving a URL-safe slug from
the name. If the request is authenticated (a valid bearer token is
presented), the new workspace's owner is set to that token's user;
otherwise the workspace is created with no owner.

#### Scenario: Creating a workspace while logged in
- **WHEN** an authenticated user submits the workspace creation form
  with a name
- **THEN** a new workspace is created with a slug derived from the name
  (e.g. "Company X" → `company-x`), owned by that user, and the user is
  taken to that workspace

#### Scenario: Creating a workspace while logged out
- **WHEN** an unauthenticated visitor submits the workspace creation
  form with a name
- **THEN** a new workspace is created with a slug derived from the
  name, with no owner, and the visitor is taken to that workspace

#### Scenario: Duplicate name is rejected
- **WHEN** a user creates a workspace whose derived slug already belongs
  to an existing workspace
- **THEN** the backend rejects the request with a clear error stating
  the name is already in use and does not create a new workspace

#### Scenario: Missing required field is rejected
- **WHEN** a user submits the workspace creation form without a name
- **THEN** the backend responds with a clear validation error and does
  not create a workspace

#### Scenario: Creating a workspace with a description
- **WHEN** a user submits the workspace creation form with a name and a
  description
- **THEN** a new workspace is created with that description stored
  alongside it

#### Scenario: Creating a workspace without a description
- **WHEN** a user submits the workspace creation form with a name and no
  description
- **THEN** a new workspace is created with an empty description, and
  creation is not blocked by the missing description

### Requirement: A workspace's description is shown on the workspaces list
The system SHALL include each workspace's description in workspace list and
detail responses, and SHALL render it below that workspace's title on the
`/workspaces` page as sanitized Markdown with line breaks preserved.

#### Scenario: Workspace with a description appears on the list
- **WHEN** a user navigates to `/workspaces` and a listed workspace has a
  non-empty description
- **THEN** that workspace's description is displayed below its title,
  rendered as sanitized Markdown

#### Scenario: Workspace without a description appears on the list
- **WHEN** a user navigates to `/workspaces` and a listed workspace has an
  empty description
- **THEN** that workspace is listed with no description content shown

### Requirement: Workspace responses reveal editability and owner presence, not owner identity
The system SHALL include a computed `can_edit` boolean and a computed
`has_owner` boolean on every workspace returned from the workspace
list and workspace detail endpoints. `can_edit` SHALL reflect whether
the current request (based on its own optional bearer token, if any)
is allowed to add or remove content in that workspace. `has_owner`
SHALL reflect whether the workspace has any owner at all, computed
identically regardless of who is asking or whether they are that
owner. The system SHALL NOT include the owner's identity (user id,
email, or any other identifying field) in these responses.

#### Scenario: Owner sees can_edit true
- **WHEN** the user who owns a workspace requests that workspace's
  details with a valid bearer token
- **THEN** the response includes `can_edit: true`

#### Scenario: Non-owner sees can_edit false
- **WHEN** a different authenticated user (not the owner), or an
  unauthenticated visitor, requests an owned workspace's details
- **THEN** the response includes `can_edit: false`

#### Scenario: Anyone sees can_edit true for an ownerless workspace
- **WHEN** any visitor, authenticated or not, requests the details of a
  workspace that has no owner
- **THEN** the response includes `can_edit: true`

#### Scenario: Owner identity is never present in the response
- **WHEN** a workspace is created, listed, or fetched by slug, by
  anyone
- **THEN** the response body does not include the owning user's id,
  email, or any other identifying field

#### Scenario: Owned workspace reports has_owner true regardless of viewer
- **WHEN** any visitor, authenticated as the owner, as a different
  user, or unauthenticated, requests the details of a workspace that
  has an owner
- **THEN** the response includes `has_owner: true`

#### Scenario: Ownerless workspace reports has_owner false regardless of viewer
- **WHEN** any visitor, authenticated or not, requests the details of a
  workspace that has no owner
- **THEN** the response includes `has_owner: false`

### Requirement: A user can browse existing workspaces
The system SHALL serve a page at `/workspaces` listing existing
workspaces by name, most recently created first, each linking to that
workspace, and linking to `/workspaces/new` to create another.

#### Scenario: Listing existing workspaces
- **WHEN** a user navigates to `/workspaces`
- **THEN** the page loads successfully and displays every existing
  workspace's name with a link into that workspace, ordered from most
  to least recently created

#### Scenario: No workspaces exist yet
- **WHEN** a user navigates to `/workspaces` before any workspace has been
  created
- **THEN** the page loads successfully and indicates there are no
  workspaces yet, with a link to create one

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
