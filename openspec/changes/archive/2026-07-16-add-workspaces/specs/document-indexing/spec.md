## MODIFIED Requirements

### Requirement: Uploaded PDFs are indexed in the background
After a PDF is successfully uploaded and stored for a workspace, the
system SHALL trigger indexing of that file in the background, without
delaying the upload's HTTP response, writing the resulting chunks and
embeddings to the `chunks` table scoped to that workspace.

#### Scenario: Upload response is not delayed by indexing
- **WHEN** a user uploads a valid PDF to a workspace
- **THEN** the upload endpoint returns its success response before
  indexing of that file necessarily completes

#### Scenario: Uploaded file becomes indexed
- **WHEN** background indexing of an uploaded PDF completes successfully
- **THEN** the content of that PDF is retrievable through the
  question-answering capability, scoped to its workspace, and the file's
  `status` becomes `indexed`

### Requirement: Chunks and embeddings are persisted in Postgres and survive container restarts
The system SHALL persist indexed chunk text and embeddings as rows in the
`chunks` table (Postgres, with a `pgvector` `embedding` column), which is
durable across backend container restarts (not just across uploads within
a single running container).

#### Scenario: Chunks persist across uploads
- **WHEN** a second PDF is uploaded and indexed after a first one, within
  the same workspace
- **THEN** content from both PDFs remains retrievable through the
  question-answering capability for that workspace

#### Scenario: Chunks persist across a container restart
- **WHEN** the backend container is stopped and started again (e.g.
  `docker compose down` followed by `docker compose up`, without removing
  the Postgres volume)
- **THEN** content from previously indexed PDFs remains retrievable
  through the question-answering capability without those files being
  re-indexed

### Requirement: The index is incrementally synced on every backend startup
On backend startup, the system SHALL ensure every file with `status`
`pending` (across all workspaces) gets indexed, using the `files.status`
column to determine what still needs indexing, and leaving files already
`status: indexed` untouched.

#### Scenario: Startup sync covers all existing pending uploads
- **WHEN** the backend starts with files whose `status` is `pending`
- **THEN** those files are indexed, their `status` becomes `indexed`, and
  their content becomes retrievable, without requiring them to be
  re-uploaded

#### Scenario: Already-indexed files are not re-indexed on startup
- **WHEN** the backend restarts and every file's `status` is already
  `indexed`
- **THEN** startup sync does not re-embed or re-index any of those files

#### Scenario: Startup does not block the server from accepting requests
- **WHEN** the backend is starting and startup sync is still in progress
- **THEN** endpoints such as `/health` respond normally without waiting
  for the sync to finish

### Requirement: Indexing progress is logged to the console
The system SHALL log the start and completion of both per-upload indexing
and the startup sync to the console, including whether each attempt
succeeded or failed, and how many files were already indexed versus newly
indexed at startup. The system SHALL NOT provide a UI or API for indexing
status beyond the `files.status` column in this change.

#### Scenario: Console shows startup sync progress
- **WHEN** the backend starts and begins syncing pending files
- **THEN** a log line reports how many files were found pending, how many
  were already indexed, and how many will be newly indexed, and a further
  log line marks completion

#### Scenario: Console shows per-upload indexing progress
- **WHEN** a background indexing job for an uploaded file finishes
  (successfully or not)
- **THEN** a log line reports the outcome for that file

### Requirement: Indexing failures do not crash the backend
The system SHALL catch and log errors encountered while parsing or
indexing a document, setting that file's `status` to `failed`, without
stopping the backend process or affecting other endpoints or other
workspaces.

#### Scenario: A single bad file does not stop indexing of others
- **WHEN** one file fails to index during a startup sync that covers
  multiple files
- **THEN** the failure is logged, that file's `status` becomes `failed`,
  and indexing continues for the remaining files
