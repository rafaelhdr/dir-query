## Purpose

The llm-provider-selection capability lets a deployer choose which provider
the backend uses for embeddings and for LLM completions, independently,
via environment variables (`EMBED_PROVIDER`, `LLM_PROVIDER`), validated at
backend startup. It supports the existing defaults (a local embedding
model, and MiniMax for completions) alongside Gemini as an alternative
provider for both, authenticated via a `GOOGLE_API_KEY` credential.

## Requirements

### Requirement: The embedding provider is selectable via `EMBED_PROVIDER`
The system SHALL determine which embedding provider it uses to embed
document content and queries from the `EMBED_PROVIDER` environment
variable, which SHALL accept `cpu` (a locally-run model, requiring no
external API credentials) or `gemini` (Google's Gemini embeddings API),
defaulting to `cpu` when unset.

#### Scenario: Default embedding provider requires no configuration
- **WHEN** the backend starts with `EMBED_PROVIDER` unset
- **THEN** embeddings are generated using the local embedding model, and no
  external embedding API credential is required

#### Scenario: Deployer opts into Gemini embeddings
- **WHEN** the backend starts with `EMBED_PROVIDER=gemini` and a valid
  `GOOGLE_API_KEY` configured
- **THEN** embeddings for newly indexed documents and for queries are
  generated using the Gemini embeddings API instead of the local model

### Requirement: The LLM provider is selectable via `LLM_PROVIDER`
The system SHALL determine which LLM provider it uses to generate answers
to questions from the `LLM_PROVIDER` environment variable, which SHALL
accept `minimax` or `gemini`, defaulting to `minimax` when unset.

#### Scenario: Default LLM provider matches current behavior
- **WHEN** the backend starts with `LLM_PROVIDER` unset
- **THEN** questions are answered using the MiniMax API, as before this
  capability existed

#### Scenario: Deployer opts into Gemini for completions
- **WHEN** the backend starts with `LLM_PROVIDER=gemini` and a valid
  `GOOGLE_API_KEY` configured
- **THEN** questions submitted to `/ask` are answered using the Gemini API
  instead of MiniMax

### Requirement: Embedding and LLM providers are selected independently
The system SHALL allow `EMBED_PROVIDER` and `LLM_PROVIDER` to be set to any
combination of their respective allowed values, without one constraining
the other.

#### Scenario: Mixed providers
- **WHEN** the backend starts with `EMBED_PROVIDER=cpu` and
  `LLM_PROVIDER=gemini` (or the reverse combination,
  `EMBED_PROVIDER=gemini` and `LLM_PROVIDER=minimax`)
- **THEN** the backend starts successfully and each capability (indexing,
  question-answering) uses its own configured provider

### Requirement: An unrecognized provider value fails backend startup
The system SHALL validate `EMBED_PROVIDER` and `LLM_PROVIDER` against their
allowed values when the backend starts, and SHALL fail startup with a clear
error naming the invalid value and the allowed values if either variable is
set to anything else.

#### Scenario: Typo'd provider value is caught immediately
- **WHEN** the backend is started with `EMBED_PROVIDER` or `LLM_PROVIDER`
  set to a value other than its allowed values
- **THEN** the backend process fails to start, with an error message
  identifying the invalid variable, its value, and the allowed values

### Requirement: Gemini is authenticated via a `GOOGLE_API_KEY` credential
The system SHALL read a Gemini API key from a `GOOGLE_API_KEY` credential,
resolved the same way `MINIMAX_API_KEY` is resolved (a file-based secret
preferred, with a plain environment variable fallback), and SHALL use it to
authenticate any Gemini embedding or completion calls.

#### Scenario: Gemini key supplied via secrets file
- **WHEN** a `GOOGLE_API_KEY` secrets file is present and non-empty, and
  either provider is set to `gemini`
- **THEN** the backend uses the key from that file to authenticate Gemini
  API calls

#### Scenario: Gemini key supplied via plain environment variable fallback
- **WHEN** no `GOOGLE_API_KEY` secrets file is present but the
  `GOOGLE_API_KEY` environment variable is set, and either provider is set
  to `gemini`
- **THEN** the backend uses the environment variable's value to
  authenticate Gemini API calls

### Requirement: Selecting Gemini without a configured credential fails clearly, without crashing the backend
The system SHALL, when `EMBED_PROVIDER` or `LLM_PROVIDER` is `gemini` and no
`GOOGLE_API_KEY` is configured, report a clear configuration error for the
affected operation (indexing a file, or answering a question) without
crashing the backend process or affecting unrelated requests.

#### Scenario: Indexing with Gemini embeddings selected but no key configured
- **WHEN** `EMBED_PROVIDER=gemini` and no `GOOGLE_API_KEY` is configured,
  and a file is uploaded
- **THEN** indexing of that file fails with a logged, clear error and the
  file's status becomes `failed`, and the backend process keeps running
  and continues to serve other requests

#### Scenario: Asking a question with Gemini completions selected but no key configured
- **WHEN** `LLM_PROVIDER=gemini` and no `GOOGLE_API_KEY` is configured, and
  a user submits a question
- **THEN** the `/ask` endpoint returns a clear configuration error response
  and does not crash the backend process

### Requirement: A manual reset script re-embeds existing content when the embedding provider changes
The system SHALL provide an operational script that a deployer can run
after changing `EMBED_PROVIDER` on a deployment with existing indexed
content. Running it SHALL clear all existing chunks, resize the chunks
table's embedding storage to match the newly configured provider's actual
output dimension, and mark all files for re-indexing, so that subsequent
indexing produces embeddings consistent with the newly configured provider
only. The system SHALL NOT attempt to automatically detect a provider
change and run this reset on its own.

#### Scenario: Deployer switches embedding provider on a deployment with existing data
- **WHEN** a deployer changes `EMBED_PROVIDER` on a deployment that already
  has indexed chunks, and runs the reset script
- **THEN** existing chunks are cleared, the embedding storage is resized to
  match the new provider's output dimension, and previously indexed files
  are eligible to be re-indexed under the new provider

#### Scenario: Re-indexing after a reset happens automatically on next sync
- **WHEN** the reset script has completed and the backend is (re)started
- **THEN** the existing incremental startup sync indexes every file marked
  for re-indexing, using the newly configured embedding provider, without
  requiring a separate manual re-indexing trigger

#### Scenario: A provider change without running the reset script fails clearly, not silently
- **WHEN** `EMBED_PROVIDER` is changed on a deployment with existing chunks
  and the reset script has not been run
- **THEN** indexing or querying against the mismatched embedding storage
  fails with a clear error rather than silently returning results computed
  from incompatible embeddings
