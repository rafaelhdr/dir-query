## Context

The home page (`frontend/public/index.html`, duplicated byte-for-byte at
`frontend/public/home/index.html`) currently pitches the product in the
abstract: it explains RAG and the workspace concept but shows no real
example, and gives no indication the project is open source. Two
workspaces already exist for demonstration purposes (`rafaelhdr-cv`,
`the-sweet-fellowship`), and the GitHub repo (`rafaelhdr/dir-query`) is
public. `openspec/specs/home-page/spec.md` currently requires identical
content be served at both `/` and `/home`; that requirement is being
dropped as part of this change, not just its implementation.

## Goals / Non-Goals

**Goals:**
- Make the hero show two real, clickable example workspaces instead of a
  single generic "browse or create" CTA.
- State plainly that the project is open source, link to the actual repo,
  and give a direct path to self-hosting/trying it (`/workspaces/new`).
- Name the concrete technologies behind the product (RAG, llama-index,
  Alpine.js, FastAPI, SDD/OpenSpec) without turning the page into a
  SaaS-style badge wall (DESIGN.md's stated anti-goal).
- Serve the home page at `/` only, removing the `/home` duplicate route.

**Non-Goals:**
- No changes to the Origami Geometric visual system itself (colors, type,
  fold-cut shapes, zig-zag layout mechanics, hero entrance animation) —
  this change is content and routing only.
- No redirect from `/home` to `/`. The project has not launched widely
  enough for old links to matter, so a plain 404 is an accepted trade-off
  over adding nginx redirect config for a route that's being retired.
- No change to how workspaces are created, listed, or queried — the ask
  page and `/workspaces/new` form are consumed as-is.

## Decisions

**Two Primary-styled hero buttons instead of one.** DESIGN.md reserves the
Button (Primary) component for "the one primary action on a page." This
page now has three candidate actions (two example links, one "test your
own workspace" CTA). Making the two example buttons Primary and demoting
"Test your own workspace" to Secondary was a deliberate call: the example
links are what actually proves the product works to a first-time visitor,
which is the page's real job, while "build your own" is a secondary
follow-up action for visitors who are already convinced. Alternatives
considered: making only one example Primary (arbitrary — no reason to
prefer one demo workspace over the other), or making all three Primary
(directly violates DESIGN.md's one-accent-emphasis rule and would read as
three competing CTAs).

**Workspace example links point directly at `/w/<slug>/ask`,** matching
the existing route pattern used elsewhere (e.g. `workspaces/new`'s submit
handler navigates to the same shape). No new routing needed.

**No outbound links on the "Technologies behind" names.** Considered
linking each of RAG/llama-index/Alpine.js/FastAPI/SDD to its docs, but
DESIGN.md explicitly warns against the page reading like "a funded SaaS
startup" — a row of five outbound badge-links tips that way. The GitHub
repo link stays, in the "Can I use it?" section, because it's the one
outbound link that directly backs a factual claim (open source) rather
than decorating a tech-stack list.

**`/home` removal is a hard delete, not a redirect.** Simpler, and
consistent with the decision to keep `/home` out of the spec entirely
rather than documenting it as deprecated-but-supported.

## Risks / Trade-offs

- **[Visitors with an old `/home` bookmark or external link get a 404]** →
  Accepted; the project has no significant external backlinks yet, and a
  redirect can be added later at near-zero cost if that changes.
- **[Hero space is now split three ways: intro paragraph, workspace
  definition, and two buttons]** → Mitigated by keeping the workspace
  definition to one short clause rather than a separate paragraph, so the
  hero doesn't grow substantially taller than today's version.
- **[The two demo workspaces (`rafaelhdr-cv`, `the-sweet-fellowship`) are
  a hard-coded content choice, not configurable]** → Acceptable for a
  small, single-operator deployment; no capability regression versus
  today's page, which also hard-codes its copy.

## Migration Plan

No data or backend migration. Deploy is a static-asset swap: replace
`frontend/public/index.html`, delete `frontend/public/home/`, update
`frontend/public/partials/nav.html`. Rollback is reverting the commit —
no state is created or destroyed by this change.

## Open Questions

None outstanding — all decisions above were confirmed during the grilling
session that produced this change.
