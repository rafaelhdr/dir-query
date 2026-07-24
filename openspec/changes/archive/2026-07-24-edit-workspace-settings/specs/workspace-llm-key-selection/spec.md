## MODIFIED Requirements

### Requirement: A workspace chooses between the system's shared LLM key and a dedicated key, changeable after creation
The system SHALL let a workspace select a `key_source` of either `system`
(the backend's shared LLM credentials, default) or `dedicated` (a
credential the workspace owner supplies), both at creation time and,
afterward, via the workspace settings page (see `workspace-management`).
An editor with `can_edit` access to the workspace MAY change `key_source`
in either direction (`system` → `dedicated` or `dedicated` → `system`) at
any time, and MAY change the provider and/or credential while remaining
`dedicated`.

#### Scenario: Default is the system key
- **WHEN** a workspace is created without specifying a key source
- **THEN** the workspace's `key_source` is `system`, and question-answering
  for that workspace uses the backend's shared LLM credentials, unchanged
  from current behavior

#### Scenario: Owner opts into a dedicated key at creation
- **WHEN** a workspace is created with `key_source=dedicated`, a chosen
  provider (`gemini` or `minimax`), and a non-empty credential
- **THEN** the workspace is created with `key_source=dedicated` and the
  chosen `key_provider`, and its dedicated credential is stored encrypted

#### Scenario: Editor switches an existing workspace from system to dedicated
- **WHEN** an editor saves the settings page with `key_source=dedicated`,
  a chosen provider, and a non-empty credential, for a workspace
  previously on `key_source=system`
- **THEN** the workspace's `key_source` becomes `dedicated` with that
  provider, and its credential is stored encrypted

#### Scenario: Editor switches an existing workspace from dedicated to system
- **WHEN** an editor saves the settings page with `key_source=system` for
  a workspace previously on `key_source=dedicated`
- **THEN** the workspace's `key_source` becomes `system` and question-
  answering for that workspace uses the backend's shared LLM credentials

## REMOVED Requirements

### Requirement: A dedicated key choice is fixed at creation
**Reason**: Superseded by the modified requirement above — `key_source`
and `key_provider` can now be changed after creation via the workspace
settings page, restricted to editors the same way other workspace edits
are.
**Migration**: No data migration needed; existing workspaces keep their
current `key_source`/`key_provider`/credential unchanged until an editor
explicitly edits them via the new settings page.

## ADDED Requirements

### Requirement: Switching from a dedicated key to the system key discards the stored credential
The system SHALL, when an editor changes a workspace's `key_source` from
`dedicated` to `system`, immediately delete that workspace's stored
encrypted credential rather than retaining it for a possible future
switch back.

#### Scenario: Credential is cleared on switch to system
- **WHEN** an editor changes a workspace's `key_source` from `dedicated`
  to `system` and saves
- **THEN** the workspace's previously stored encrypted credential is
  removed from the database

#### Scenario: Switching back to dedicated later requires a new credential
- **WHEN** an editor who previously switched a workspace to `system`
  later switches it back to `dedicated`
- **THEN** the request is treated as entering `dedicated` for the first
  time, requiring a provider and a non-empty credential

### Requirement: A credential is required only when entering dedicated or changing provider
The system SHALL require a non-empty credential in a settings save
request only when the request changes `key_source` from `system` to
`dedicated`, or changes `key_provider` while `key_source` remains
`dedicated`. When `key_source` stays `dedicated` and `key_provider` is
unchanged, the system SHALL accept a blank credential field and SHALL
leave the workspace's existing stored encrypted credential unchanged.

#### Scenario: Blank credential keeps the existing key when provider is unchanged
- **WHEN** an editor saves the settings page with `key_source=dedicated`,
  the same `key_provider` the workspace already has, and a blank
  credential field
- **THEN** the save succeeds and the workspace's previously stored
  encrypted credential is unchanged

#### Scenario: Blank credential is rejected when changing provider
- **WHEN** an editor saves the settings page with `key_source=dedicated`,
  a different `key_provider` than the workspace currently has, and a
  blank credential field
- **THEN** the backend rejects the request with a clear validation error
  and the workspace's `key_provider` and credential remain unchanged

#### Scenario: Blank credential is rejected when entering dedicated
- **WHEN** an editor saves the settings page with `key_source=dedicated`
  for a workspace previously on `key_source=system`, and a blank
  credential field
- **THEN** the backend rejects the request with a clear validation error
  and the workspace remains on `key_source=system`

#### Scenario: Non-empty credential while changing provider replaces the stored key
- **WHEN** an editor saves the settings page with `key_source=dedicated`,
  a different `key_provider` than the workspace currently has, and a
  non-empty credential
- **THEN** the workspace's `key_provider` and stored encrypted credential
  are both updated to the new values
