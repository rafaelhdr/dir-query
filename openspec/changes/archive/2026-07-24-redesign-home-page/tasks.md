## 1. Rewrite the home page content

- [x] 1.1 Rewrite the hero intro paragraph in `frontend/public/index.html` to explain what Dir Query does (AI over your own documents, grounded answers) and briefly define "workspace"
- [x] 1.2 Replace the hero's single "Browse or create a workspace" CTA with two `origami-button-primary` links: "rafaelhdr CV" → `/w/rafaelhdr-cv/ask` and "Fiction Company" → `/w/the-sweet-fellowship/ask`
- [x] 1.3 Replace the "What is RAG?" zig-zag row with a "Can I use it?" row: open-source/self-hostable copy with an inline link to `https://github.com/rafaelhdr/dir-query`, plus an `origami-button-secondary` "Test your own workspace" link to `/workspaces/new`
- [x] 1.4 Replace the "Workspaces" zig-zag row with a "Technologies behind" row: plain-text paragraph naming RAG, llama-index, Alpine.js, FastAPI, and SDD (OpenSpec), no outbound links
- [x] 1.5 Verify the direction-contract HTML comment at the top of `index.html` still accurately describes the page (update if the STORY/FIRST VIEWPORT description no longer matches)

## 2. Remove the /home route

- [x] 2.1 Delete `frontend/public/home/` entirely
- [x] 2.2 Update `frontend/public/partials/nav.html`'s "Home" link from `/home` to `/`
- [x] 2.3 Update `DESIGN.md` line ~105 to drop the "and `/home`" mention of the home page tier

## 3. Update specs and docs

- [x] 3.1 Confirm `openspec/specs/home-page/spec.md` delta accurately reflects the shipped content once 1.1–1.4 are done
- [x] 3.2 Confirm `openspec/specs/ask-page/spec.md` delta's "Navigating from ask to home" scenario matches the shipped nav link target (`/`)

## 4. Verify

- [x] 4.1 Run `docker compose up --build` and visually check `/` renders the new hero and two content rows correctly in both light and dark theme
- [x] 4.2 Confirm `/home` returns a 404
- [x] 4.3 Click through both example workspace buttons, the GitHub link, and "Test your own workspace" to confirm each destination is correct
- [x] 4.4 Run `openspec validate --changes redesign-home-page --strict` (or `openspec change validate redesign-home-page --strict`) to confirm the change is still valid before archiving
