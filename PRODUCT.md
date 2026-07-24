# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: visitors to the hosted/demo instance who use the public
`rafaelhdr-cv` workspace (`/w/rafaelhdr-cv/ask`) to ask natural-language
questions about rafaelhdr's experience, grounded in his CV, without
setting anything up themselves.

Secondary: anyone who self-hosts their own Dir Query instance (via the
project's `docker compose` setup) to upload their own PDFs into a
workspace and ask questions about them. Supported and designed for, but
not the project's current primary audience.

## Product Purpose

Dir Query lets someone point at a set of PDF documents, grouped into a
workspace, and ask questions about them in plain language. It uses
Retrieval-Augmented Generation (RAG): relevant pieces of the workspace's
documents are retrieved and given to an LLM so answers are grounded in
that content rather than the model's general knowledge. Success is an
accurate answer traceable to the workspace's own documents — for the
live demo specifically, a visitor getting a useful, accurate answer
about rafaelhdr's experience.

## Positioning

A small, self-hostable, open-source RAG tool — not a hosted SaaS.
Ships as a self-contained `docker compose` stack a deployer can run
with their own API keys. LLM and embedding providers are independently
swappable (MiniMax default for completions, Gemini as an alternative
for both; the default embedding model runs locally on CPU, needing no
API key at all) rather than locking to one vendor. Documents are
strictly isolated per workspace, so different document sets never mix.

## Operating Context

Workspaces are created/browsed at `/workspaces`; questions are asked at
`/w/<slug>/ask` with conversation history retained per workspace;
files are uploaded and managed at `/w/<slug>/feed/files`. The public
deployment anchors on one demo workspace, `rafaelhdr-cv`, linked from
the About page as the primary way visitors interact with the live
instance. Runs via `docker compose`: FastAPI + Postgres/pgvector
backend, static Alpine.js frontend served by Nginx. Built through
OpenSpec spec-driven changes (see `openspec/specs/`).

## Capabilities and Constraints

- Uploads accept PDF only. Indexing runs in the background after
  upload (chunks + embeddings written to Postgres/pgvector) and
  incrementally syncs on every backend startup.
- Question-answering retrieves from a workspace's indexed chunks and
  generates via the configured LLM, including up to a configurable
  number (default 10) of the most recent prior exchanges of the same
  conversation as context.
- User auth (email + password) is optional: an authenticated user owns
  and can exclusively edit the workspaces they create; workspaces
  created while unauthenticated have no owner and stay public and
  editable by anyone.
- A workspace can opt, only at creation time, into a dedicated
  (encrypted-at-rest) LLM key instead of the shared system credentials;
  this choice cannot change afterward and does not affect embeddings.
- Beta/practice status: the public instance runs on free API keys, so
  it can be slow or occasionally fail to respond. A beta badge in the
  header discloses this on every page.

## Brand Commitments

Name: **Dir Query**. Built and maintained by rafaelhdr
(https://www.rafaelhdr.com.br/), a solo developer with a DevOps
background, as a practice project to learn Spec-Driven Development and
RAG by shipping something real. Open source at
github.com/rafaelhdr/dir-query. A beta badge is shown in the site
header on every page.

## Evidence on Hand

The live public demo workspace at `/w/rafaelhdr-cv/ask`, pointed at
rafaelhdr's CV, is the project's concrete evidence and showcase — this
is the only real customer-facing content that exists. Do not fabricate
other customers, testimonials, case studies, pricing, or licensing
claims; none exist beyond "open source" on GitHub.

## Product Principles

1. Grounded answers over generic ones — every answer must trace back
   to retrieved content from the workspace's own documents.
2. Self-hostable and provider-agnostic — never hard-couple to one
   LLM/embedding vendor; keep the `docker compose` footprint small and
   easy to install elsewhere.
3. Workspace isolation is absolute — document sets never mix across
   workspaces.
4. Honest about beta status — instability and processing limits
   (PDF-only, background indexing, free-tier API keys) are disclosed,
   not hidden.
5. The demo doubles as portfolio — the `rafaelhdr-cv` workspace must
   stay a credible, working showcase of both the product and its
   builder.
