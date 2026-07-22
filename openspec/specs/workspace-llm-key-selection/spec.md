## Purpose

The workspace-llm-key-selection capability lets a workspace owner choose,
at workspace creation time, whether question-answering for that workspace
uses the backend's shared LLM credentials (the `system` key source) or a
dedicated credential the owner supplies for a chosen provider (the
`dedicated` key source). This choice is fixed at creation and cannot be
changed afterward. A dedicated credential is encrypted at rest, never
returned by the API, and used only for answering questions — not for
document embedding, which continues to use the backend's globally
configured `EMBED_PROVIDER`. Key configuration is visible only to the
workspace owner.

## Requirements

### Requirement: A workspace chooses between the system's shared LLM key and a dedicated key at creation time
The system SHALL let a workspace, at creation time only, select a
`key_source` of either `system` (the backend's shared LLM credentials,
default) or `dedicated` (a credential the workspace owner supplies). This
choice SHALL NOT be changeable after the workspace is created.

#### Scenario: Default is the system key
- **WHEN** a workspace is created without specifying a key source
- **THEN** the workspace's `key_source` is `system`, and question-answering
  for that workspace uses the backend's shared LLM credentials, unchanged
  from current behavior

#### Scenario: Owner opts into a dedicated key
- **WHEN** a workspace is created with `key_source=dedicated`, a chosen
  provider (`gemini` or `minimax`), and a non-empty credential
- **THEN** the workspace is created with `key_source=dedicated` and the
  chosen `key_provider`, and its dedicated credential is stored encrypted

### Requirement: A dedicated key requires both a provider and a non-empty credential
The system SHALL reject workspace creation with a validation error when
`key_source=dedicated` is requested without also supplying a provider
(`gemini` or `minimax`) and a non-empty credential value.

#### Scenario: Dedicated selected with no credential
- **WHEN** a workspace creation request has `key_source=dedicated` and an
  empty or missing credential
- **THEN** the backend rejects the request with a clear validation error
  and does not create the workspace

#### Scenario: Dedicated selected with no provider
- **WHEN** a workspace creation request has `key_source=dedicated` and no
  provider selected
- **THEN** the backend rejects the request with a clear validation error
  and does not create the workspace

### Requirement: A dedicated credential is encrypted at rest and never returned by the API
The system SHALL encrypt a dedicated credential before storing it, using a
key derived from a dedicated encryption secret (`WORKSPACE_KEY_ENCRYPTION_SECRET`),
resolved the same way other credential secrets are resolved (a file-based
secret preferred, with a plain environment variable fallback). The system
SHALL NOT store the credential in plaintext, and SHALL NOT include the
credential (plaintext or encrypted) in any API response.

#### Scenario: Dedicated credential is stored encrypted
- **WHEN** a workspace is created with a dedicated credential
- **THEN** the value persisted to the database is the credential encrypted
  with the configured encryption secret, not the plaintext value

#### Scenario: Credential is never exposed via the API
- **WHEN** any workspace endpoint returns a workspace that has a dedicated
  credential configured
- **THEN** the response does not include the credential in any form

#### Scenario: Encryption secret missing when a dedicated key is submitted
- **WHEN** a workspace creation request has `key_source=dedicated` and no
  `WORKSPACE_KEY_ENCRYPTION_SECRET` is configured on the backend
- **THEN** the backend responds with a clear configuration error and does
  not create the workspace or crash the backend process

### Requirement: Key configuration is visible only to the workspace owner
The system SHALL include `key_source` and `key_provider` in a workspace
response only when the requester can edit that workspace (per the
`workspace-management` capability's `can_edit` computation); other
requesters SHALL receive these fields as absent or null.

#### Scenario: Owner sees their workspace's key configuration
- **WHEN** the owner of a workspace (or anyone, for an ownerless workspace)
  requests that workspace's details
- **THEN** the response includes that workspace's `key_source` and, if
  dedicated, its `key_provider`

#### Scenario: Non-owner does not see key configuration
- **WHEN** a user who is not the workspace's owner (or an unauthenticated
  visitor, for an owned workspace) requests that workspace's details
- **THEN** the response's `key_source` and `key_provider` fields are absent
  or null

### Requirement: A dedicated key is used only for answering questions, not for embedding
The system SHALL use a workspace's dedicated key, when configured, only for
generating answers via `/w/<slug>/ask`. Document embedding and indexing
SHALL continue to use the backend's globally configured `EMBED_PROVIDER`
regardless of a workspace's `key_source`.

#### Scenario: Uploading a document to a dedicated-key workspace
- **WHEN** a file is uploaded and indexed in a workspace with
  `key_source=dedicated`
- **THEN** the file is embedded using the backend's globally configured
  `EMBED_PROVIDER`, not the workspace's dedicated key or provider

#### Scenario: Asking a question in a dedicated-key workspace
- **WHEN** a question is submitted to a workspace with
  `key_source=dedicated` and a valid credential
- **THEN** the answer is generated using that workspace's dedicated
  provider and credential instead of the backend's shared LLM credentials
</content>
