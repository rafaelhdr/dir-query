## MODIFIED Requirements

### Requirement: Question-answering uses a configurable LLM provider, defaulting to MiniMax
The system SHALL generate answer text using whichever LLM provider is
configured via `LLM_PROVIDER` (see the `llm-provider-selection`
capability), via a configured API key for that provider. By default
(`LLM_PROVIDER` unset or `minimax`), this SHALL be the MiniMax API, as
before this capability existed. When the workspace being asked has a
dedicated key configured (see the `workspace-llm-key-selection`
capability), the system SHALL use that workspace's dedicated provider and
credential instead of the globally configured `LLM_PROVIDER` and its
credential.

#### Scenario: Asking a question without a configured API key for the selected provider
- **WHEN** a user submits a question to a workspace using the system key
  while the backend has no valid API key configured for the currently
  selected `LLM_PROVIDER` (MiniMax or Gemini)
- **THEN** the endpoint returns a clear error response and does not crash
  the backend process

#### Scenario: Asking a question using the Gemini LLM provider
- **WHEN** a user submits a question to a workspace using the system key
  while `LLM_PROVIDER=gemini` and a valid `GOOGLE_API_KEY` is configured
- **THEN** the endpoint returns an answer generated using the Gemini API

#### Scenario: Asking a question in a workspace with a dedicated key
- **WHEN** a user submits a question to a workspace whose `key_source` is
  `dedicated`
- **THEN** the endpoint generates the answer using that workspace's
  configured provider and credential, regardless of the backend's globally
  configured `LLM_PROVIDER`

## ADDED Requirements

### Requirement: Each answered exchange records which key source and provider answered it
The system SHALL record, on each successfully answered exchange, which key
source (`system` or `dedicated`) and which provider (`gemini` or `minimax`)
generated its answer, reflecting the workspace's key configuration at the
moment that exchange was answered.

#### Scenario: Exchange answered using the system key
- **WHEN** a question is answered in a workspace using the system key
- **THEN** the resulting exchange records `system` as its key source and
  the provider that answered it

#### Scenario: Exchange answered using a dedicated key
- **WHEN** a question is answered in a workspace using a dedicated key
- **THEN** the resulting exchange records `dedicated` as its key source and
  the workspace's configured provider
