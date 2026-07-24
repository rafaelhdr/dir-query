## 1. Backend: slug recompute + collision handling

- [x] 1.1 Extract a shared helper (or reuse `slugify` directly) so `PATCH /workspaces/{slug}` recomputes the slug from an edited name the same way `create_workspace` does
- [x] 1.2 Add `PATCH /workspaces/{slug}` in `backend/app/api/workspaces.py`, gated by `_can_edit` (reject with the same style of error used for uploads/deletes on non-editable workspaces)
- [x] 1.3 On name change, update `slug`; catch the `IntegrityError` from the existing unique constraint and return a 409 conflict, mirroring `create_workspace`'s handling (workspaces.py:93-100), leaving the row unchanged
- [x] 1.4 Verify resubmitting a workspace's own current values (including its own current slug) succeeds and is not treated as a collision with itself (verified in tests, see section 3)

## 2. Backend: LLM key edit semantics

- [x] 2.1 Add request validation: `key_source=dedicated` requires `key_provider`; credential required only when `key_source` is entering `dedicated` from `system`, or `key_provider` is changing while staying `dedicated` — otherwise credential may be blank and the existing `encrypted_api_key` is left untouched
- [x] 2.2 On transition from `dedicated` to `system`, clear `key_provider` and `encrypted_api_key` on the row
- [x] 2.3 On a validated new credential, encrypt it via `crypto.encrypt` the same way `create_workspace` does, reusing the existing missing-encryption-secret error handling (503)
- [x] 2.4 Return the updated `WorkspacePublic` from `_workspace_public`, confirming `key_source`/`key_provider` are still withheld for non-editors per the existing `workspace-llm-key-selection` visibility rule (unchanged `_workspace_public` already applies this)

## 3. Backend tests

- [x] 3.1 Test: editor can update name/description; slug changes accordingly
- [x] 3.2 Test: rename to a name whose slug collides with another workspace is rejected with 409, nothing changed
- [x] 3.3 Test: non-editor (wrong user, or unauthenticated on an owned workspace) gets rejected, nothing changed
- [x] 3.4 Test: switching system → dedicated without a credential is rejected; with provider + credential succeeds and encrypts the credential
- [x] 3.5 Test: switching dedicated → system clears `key_provider` and the stored credential
- [x] 3.6 Test: staying dedicated with the same provider and a blank credential keeps the existing stored credential; staying dedicated but changing provider with a blank credential is rejected
- [x] 3.7 Test: resubmitting identical values (including same name/slug) succeeds

## 4. Frontend: settings page

- [x] 4.1 Add `frontend/public/w/settings/index.html`, following the existing page pattern (SSI head/nav/heading includes, Alpine `x-data` component) used by `w/feed/files/index.html` and `w/ask/index.html`
- [x] 4.2 Add an nginx location block in `frontend/nginx.conf` for `^/w/[^/]+/settings/?$` → `try_files /w/settings/index.html =404;`, alongside the existing `/w/[^/]+/feed/files/?$` and `/w/[^/]+/ask/?$` blocks
- [x] 4.3 Build the settings form: name, description, key_source selector, provider selector (shown when dedicated), credential field (optional unless entering dedicated or changing provider, per spec). Adaptation: the settings page is a single always-editable form (mirroring `/workspaces/new`'s creation form) rather than a per-field Edit/Save/Cancel toggle — there is no separate "view" state for a whole settings page to toggle out of, unlike an inline table-row rename. It keeps the inline-error-on-failure part of the precedent (`#form-error`, matching `create-workspace`'s pattern) and Enter-submits for free via native form submission; Escape-to-cancel has no natural target here and was not implemented.
- [x] 4.4 On successful save, if the returned slug differs from the current URL's slug, navigate the browser to `/w/<new-slug>/settings`; otherwise stay in place and reflect the saved values
- [x] 4.5 On failed save, keep the form in its editable state and show the backend's error message inline, without a native dialog
- [x] 4.6 As the name field is edited, compute the derived slug client-side (or debounce a check) and show an inline warning when it differs from the workspace's current slug, stating the current URL will stop working and that any existing references to it (e.g. a link in a blog post, or in the future an embedded widget) will need updating — informational only, does not block Save

## 5. Frontend: tab bar and access control

- [x] 5.1 Add a "Settings" tab (`<a :href="'/w/' + slug + '/feed/files'">`-style link to `/w/<slug>/settings`) to the tab bar markup in `w/feed/files/index.html` and `w/ask/index.html`, shown only when the fetched workspace's `can_edit` is `true`. Also applied to `w/ask/conversations/index.html`, which shares the same tab bar and wasn't explicitly called out but needed the same treatment for consistency; both `w/ask/index.html` and the conversations page previously fetched the workspace with an unauthenticated `fetch()`, which would have always computed `can_edit` as false for a logged-in owner, so both were switched to `Auth.fetch()` for this call so the Settings tab actually appears for owners.
- [x] 5.2 Mark the Settings tab as active/selected when on `/w/<slug>/settings`
- [x] 5.3 On the settings page itself, after fetching the workspace, redirect (`window.location`) to `/w/<slug>/feed/files` if `can_edit` is `false`

## 6. Verification

- [x] 6.1 Run backend test suite (`uv run pytest -v`) — 127 passed
- [x] 6.2 Manually exercised in a browser against this worktree's own isolated docker compose stack (unique ports/project name to avoid colliding with the main checkout's running stack, per AGENTS.md): registered an owner, created "Company X", renamed it to "Acme Corporation" — the slug-change warning appeared, save navigated to `/w/acme-corporation/settings`, and the old `/w/company-x/settings` URL now 404s ("Workspace not found"); switched the key from system to dedicated (Gemini, with a credential) and confirmed via the database that it was stored encrypted; switched back to system and confirmed both `key_provider` and the encrypted credential were cleared; registered a second, non-owner user and confirmed direct navigation to `/w/acme-corporation/settings` redirects to the content page, and that the Settings tab is absent from both the content and ask pages for that non-owner. Ownerless-workspace editability by an unauthenticated visitor is already covered by the automated tests (3.3) and was not repeated manually.
