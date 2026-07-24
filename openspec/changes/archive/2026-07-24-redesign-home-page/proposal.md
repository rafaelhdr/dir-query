## Why

The home page's current copy explains RAG and workspaces in the abstract, gives visitors no concrete way to see the product working, and is duplicated at both `/` and `/home` for no functional reason. New copy that shows two live example workspaces, states plainly that the project is open source and self-hostable, and names the stack behind it will make the page do more persuasive work — and dropping the redundant `/home` path removes a maintenance liability (two routes that must always stay byte-identical).

## What Changes

- Rewrite the hero intro paragraph to explain that Dir Query lets you use AI to understand your own documents and ask questions grounded in them, and to briefly define "workspace" as a separate collection of documents (e.g. per person or company).
- Replace the hero's single "Browse or create a workspace" CTA with two Primary-styled example buttons: "rafaelhdr CV" (linking to the `rafaelhdr-cv` workspace's ask page) and "Fiction Company" (linking to the `the-sweet-fellowship` workspace's ask page).
- Replace the "What is RAG?" zig-zag row with a "Can I use it?" row: confirms the project is open source and self-hostable, links the open-source claim to the GitHub repo, and adds a Secondary-styled "Test your own workspace" button linking to `/workspaces/new`.
- Replace the "Workspaces" zig-zag row with a "Technologies behind" row: a short plain-text paragraph naming RAG, llama-index, Alpine.js, FastAPI, and SDD (Spec-Driven Development, this repo's own OpenSpec workflow).
- **BREAKING**: Remove the `/home` route entirely — delete `frontend/public/home/`, and update `frontend/public/partials/nav.html`'s "Home" link to point to `/`. The home page is now reachable only at `/`. No redirect is added; visitors with an old `/home` link get a 404.
- Update `DESIGN.md` and the `ask-page` spec's references to `/home` to reflect the single `/` route.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `home-page`: drop the requirement to serve identical content at both `/` and `/home` (now `/` only); rewrite the content requirement to describe the new three-section structure (what Dir Query is + workspace definition + two example links, open-source/self-hostable pitch with a repo link and a "create your own" CTA, and a technologies-used summary) in place of the old RAG-explanation/workspace-explanation requirement.
- `ask-page`: update the requirement/scenario describing navigation back to the home page so it points at `/` instead of `/home`.

## Impact

- `frontend/public/index.html` — full content rewrite.
- `frontend/public/home/` — deleted.
- `frontend/public/partials/nav.html` — "Home" link target changed from `/home` to `/`.
- `DESIGN.md` — drop the `/home` mention in the home-page tier description.
- `openspec/specs/home-page/spec.md`, `openspec/specs/ask-page/spec.md` — requirement/scenario updates described above.
- No backend or API impact.
