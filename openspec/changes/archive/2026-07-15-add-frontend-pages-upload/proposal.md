## Why

The application currently only has a placeholder "Hello world" frontend and a backend with a health check. To move toward the product (a RAG — Retrieval-Augmented Generation — assistant over the user's documents), we need the first user-facing surface: an explanation of the project, a place to eventually ask questions, and a way to start feeding documents into the system. This change delivers that beta-stage surface without yet wiring up any RAG logic.

## What Changes

- Add a **home page** (`/`) explaining the project and briefly what RAG is, with a clear "Beta" notice.
- Add an **ask page** (`/ask`) with a bottom input box for questions. Submitting does nothing yet (no backend wiring) — it exists as the future home for RAG Q&A.
- Add an **upload page** (`/feed/upload`) where the user can push PDF documents to the server.
- Add a backend endpoint that accepts PDF uploads and stores them to a repo-local folder (bind-mounted into the backend container), so uploaded files are easy to find directly on disk. No parsing, indexing, or processing of uploaded files happens in this change.
- Uploads are write-only: users can push new files, but there is no listing, download, update, or delete (no CRUD) yet.
- Only PDF files are accepted; other file types are rejected.
- Add simple navigation between the three pages.

## Capabilities

### New Capabilities
- `home-page`: Static informational home page — project description, brief explanation of RAG, and a beta notice.
- `ask-page`: Placeholder Q&A page with a question input; no backend integration yet.
- `document-upload`: Upload page plus backend API to accept PDF files and persist them to disk. Upload-only, PDF-only, no CRUD.

### Modified Capabilities
_None — this is the first feature-level change; no existing specs are affected._

## Impact

- `frontend/`: new static pages/routes (`/`, `/ask`, `/feed/upload`) and shared navigation.
- `backend/`: new upload router/endpoint, PDF validation, file storage to a configurable directory.
- `docker-compose.yml`: new bind mount (`./backend/data/uploads`) for uploaded files, mounted into the backend service.
- No changes to existing `health` capability or docs setup.
