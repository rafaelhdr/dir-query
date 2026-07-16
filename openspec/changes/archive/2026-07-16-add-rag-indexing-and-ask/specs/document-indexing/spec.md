## ADDED Requirements

### Requirement: Uploaded PDFs are indexed in the background
After a PDF is successfully uploaded and stored, the system SHALL trigger indexing of that file in the background, without delaying the upload's HTTP response.

#### Scenario: Upload response is not delayed by indexing
- **WHEN** a user uploads a valid PDF
- **THEN** the upload endpoint returns its success response before indexing of that file necessarily completes

#### Scenario: Uploaded file becomes indexed
- **WHEN** background indexing of an uploaded PDF completes successfully
- **THEN** the content of that PDF is retrievable through the question-answering capability

### Requirement: The index is persisted to disk and survives container restarts
The system SHALL persist the document index to a directory on disk that is durable across backend container restarts (not just across uploads within a single running container).

#### Scenario: Index persists across uploads
- **WHEN** a second PDF is uploaded and indexed after a first one
- **THEN** content from both PDFs remains retrievable through the question-answering capability

#### Scenario: Index persists across a container restart
- **WHEN** the backend container is stopped and started again (e.g. `docker compose down` followed by `docker compose up`)
- **THEN** content from previously indexed PDFs remains retrievable through the question-answering capability without those files being re-indexed

### Requirement: The index is incrementally synced on every backend startup
On backend startup, the system SHALL ensure every PDF currently present in the upload folder is indexed, indexing only files not already represented in the persisted index and leaving already-indexed files untouched.

#### Scenario: Startup sync covers all existing uploads
- **WHEN** the backend starts with PDFs already present in the upload folder that have never been indexed
- **THEN** those PDFs are indexed and their content becomes retrievable, without requiring them to be re-uploaded

#### Scenario: Already-indexed files are not re-indexed on startup
- **WHEN** the backend restarts and every PDF in the upload folder is already represented in the persisted index
- **THEN** startup sync does not re-embed or re-index any of those files

#### Scenario: Startup does not block the server from accepting requests
- **WHEN** the backend is starting and startup sync is still in progress
- **THEN** endpoints such as `/health` respond normally without waiting for the sync to finish

### Requirement: Indexing progress is logged to the console
The system SHALL log the start and completion of both per-upload indexing and the startup sync to the console, including whether each attempt succeeded or failed, and how many files were already indexed versus newly indexed at startup. The system SHALL NOT provide a UI or API for indexing status in this change.

#### Scenario: Console shows startup sync progress
- **WHEN** the backend starts and begins syncing the index
- **THEN** a log line reports how many uploads were found, how many were already indexed, and how many will be newly indexed, and a further log line marks completion

#### Scenario: Console shows per-upload indexing progress
- **WHEN** a background indexing job for an uploaded file finishes (successfully or not)
- **THEN** a log line reports the outcome for that file

### Requirement: Indexing uses a local embedding model, requiring no external API credentials
The system SHALL generate embeddings for indexed document content using a locally-run embedding model, without requiring any external API key.

#### Scenario: Indexing succeeds without any MiniMax credentials configured
- **WHEN** the backend indexes an uploaded PDF while no MiniMax API key is configured
- **THEN** indexing completes successfully, since embeddings do not depend on MiniMax

### Requirement: Indexing failures do not crash the backend
The system SHALL catch and log errors encountered while parsing or indexing a document, leaving that document simply un-indexed, without stopping the backend process or affecting other endpoints.

#### Scenario: A single bad file does not stop indexing of others
- **WHEN** one file fails to index during a startup sync that covers multiple files
- **THEN** the failure is logged and indexing continues for the remaining files
