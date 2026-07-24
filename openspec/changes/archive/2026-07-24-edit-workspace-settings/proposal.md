## Why

A workspace's name, description, and LLM key configuration can currently only be set once, at creation. There is no way to fix a typo in a name, update a description, or rotate/change an LLM credential without recreating the workspace and losing its content. Editors (owners, or anyone on an ownerless workspace) need a way to change these after the fact, using the same permission model already enforced for adding and deleting content.

## What Changes

- Add a workspace settings page at `/w/<slug>/settings`, reachable via a new "Settings" tab in the existing Ask/Content tab bar, visible only when the current visitor's `can_edit` is true for that workspace. A visitor without edit access who loads the URL directly is redirected to the workspace's content page.
- Add `PATCH /workspaces/{slug}`, a full-submission endpoint (the settings form always sends the complete current state, not a partial diff), restricted the same way workspace content edits already are: rejected for a non-editor.
- Editing the name recomputes the workspace's slug using the same slugify logic as creation. A recomputed slug that collides with another workspace's existing slug is rejected with a conflict error, changing nothing. There is no redirect/alias kept for a slug that changes — the old URL simply stops resolving. On a successful save that changes the slug, the frontend navigates the browser to the new `/w/<new-slug>/settings` URL.
- **BREAKING**: `key_source`/`key_provider` are no longer fixed at creation. An editor can switch between `system` and `dedicated` in either direction, and while `dedicated`, change provider and/or replace the credential. Switching from `dedicated` to `system` immediately discards the previously stored encrypted credential. A credential value is required in the request only when switching into `dedicated` for the first time or when changing provider while already `dedicated`; otherwise it may be left blank to keep the existing stored credential (the API never returns it for resubmission).
- Settings form fields follow the existing inline-edit UX precedent (Edit/Save/Cancel, Enter=Save, Escape=Cancel, failed save keeps the field open with an inline error instead of a native dialog).

## Capabilities

### New Capabilities
(none — this folds into the existing `workspace-management` capability)

### Modified Capabilities
- `workspace-management`: adds the ability to edit an existing workspace's name, description, and LLM key configuration via a new settings page and `PATCH /workspaces/{slug}` endpoint, including slug recomputation/collision handling on rename and the settings-tab visibility rule.
- `document-upload`: the content page's tab bar requirement changes from two tabs (Ask, Content) to three (Ask, Content, Settings), with Settings shown only when `can_edit` is true.
- `workspace-llm-key-selection`: removes the requirement that `key_source`/`key_provider` are fixed at creation and cannot be changed; replaces it with requirements describing how they can be edited afterward, including credential/discard semantics.

## Impact

- Backend: new `PATCH /workspaces/{slug}` route in `backend/app/api/workspaces.py`, reusing/extending the existing `_can_edit` check; slug recomputation and collision handling reused from workspace creation; key-source transition logic (discard-on-switch-to-system, conditional credential requirement) added alongside the existing encryption logic in `crypto`.
- Frontend: new `/w/<slug>/settings` page under `frontend/public/`, using the existing partials (head/nav/heading) and tab-bar pattern; tab bar partial/markup updated to include the conditional Settings tab.
- Specs: delta edits to `workspace-management`, `document-upload`, and `workspace-llm-key-selection`.
