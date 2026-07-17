## MODIFIED Requirements

### Requirement: Question-answering uses a configurable LLM provider, defaulting to MiniMax
The system SHALL generate answer text using whichever LLM provider is
configured via `LLM_PROVIDER` (see the `llm-provider-selection`
capability), via a configured API key for that provider. By default
(`LLM_PROVIDER` unset or `minimax`), this SHALL be the MiniMax API, as
before this capability existed.

#### Scenario: Asking a question without a configured API key for the selected provider
- **WHEN** a user submits a question while the backend has no valid API key
  configured for the currently selected `LLM_PROVIDER` (MiniMax or Gemini)
- **THEN** the endpoint returns a clear error response and does not crash
  the backend process

#### Scenario: Asking a question using the Gemini LLM provider
- **WHEN** a user submits a question while `LLM_PROVIDER=gemini` and a
  valid `GOOGLE_API_KEY` is configured
- **THEN** the endpoint returns an answer generated using the Gemini API
