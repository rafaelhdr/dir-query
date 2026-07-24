---
name: Dir Query
description: A self-hostable RAG tool for asking questions about your own documents
colors:
  paper: "#FAFAFA"
  ink: "#1A1A1A"
  steel: "#4A4A4A"
  fold-shadow: "#B0B0B0"
  coral: "#FF6B6B"
  coral-ink: "#B34B4B"
  coral-light: "#ff8a8a"
  sky: "#87CEEB"
  sage: "#A8D5BA"
  crease: "#F0C987"
typography:
  hero:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 5vw, 4rem)"
    fontWeight: 700
    lineHeight: 1.1
  h1:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1.2
  h2:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.3
  h2-operate:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  body-lg:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Poppins, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.3
  mono:
    fontFamily: "ui-monospace, 'SF Mono', 'Cascadia Code', 'Roboto Mono', monospace"
    fontSize: "0.9em"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  none: "0"
shapes:
  cut-sm: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 0 100%)"
  cut-lg: "polygon(0 0, calc(100% - 20px) 0, 100% 20px, 100% 100%, 0 100%)"
  cut-lg-mirror: "polygon(20px 0, 100% 0, 100% 100%, 0 100%, 0 20px)"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.coral}"
    textColor: "{colors.ink}"
    shape: "{shapes.cut-sm}"
    padding: "0.65rem 1.25rem"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    shape: "{shapes.cut-sm}"
    padding: "0.35rem 0.7rem"
  source-chip:
    backgroundColor: "transparent"
    textColor: "{colors.coral-ink}"
    shape: "{shapes.cut-sm}"
    padding: "0.15rem 0.5rem"
  beta-mark:
    backgroundColor: "transparent"
    textColor: "{colors.coral}"
    shape: "{shapes.cut-sm}"
    padding: "0.1rem 0.5rem"
  text-input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0.5rem"
---

# Design System: Dir Query

## Overview

**Creative North Star: "Origami Geometric"**

Dir Query's visual identity is built from a single physical idea: a flat sheet becomes dimensional through precise, deliberate folds — never a cut, never an arbitrary flourish. Every accented shape on the site carries one clipped corner (the "fold cut"), the same signature device a paper crease would leave, and it appears only where it means something: buttons you press, source citations you follow, the beta mark. Passive containers — cards, entry blocks, list rows, the input field — stay plain rectangles, so the cut stays legible as a deliberate accent instead of decorating everything it touches.

This world now governs the entire site, at two intensities:
- **Full expression — the home page** (`/` and `/home`, Persuade mode): the hero, the crease-line tessellation texture, the split-screen and zig-zag layout, the one authored entrance animation.
- **Restrained expression — every other page** (Operate/Read mode): the same tokens, type, and fold-cut device, but no tessellation, no hero, no entrance motion. This covers the ask page (`/w/<slug>/ask`), workspaces list and creation, login/register, about/beta, past conversations, and the content/files manager — an Operate or Read surface earns scanability over expression, and the anti-goals for this project (don't look like a funded SaaS startup, don't over-design something this small) apply hardest here.

This world replaces "The Lab Notebook," which briefly governed the ask page alone. The lamp-falloff palette and dated-entry conceit are fully retired — no `lamp-*` or `red-pen` token survives this pass. The prior bare/unstyled baseline (documented in an earlier revision as "Legacy") is also fully retired: every page in the app now carries this system, so no `legacy-*` token or bare/unscoped CSS selector remains — this file no longer needs a parallel "Legacy" track.

**Key Characteristics:**
- One functional accent (Coral) reserved for interactive elements; three decorative hues (Sky, Sage, Warm Crease) appear only inside the hero's crease-line texture — never on text, controls, or anything load-bearing.
- The fold-cut corner is the system's one recurring shape device, reserved for buttons, source chips, and the beta mark — never applied to passive containers.
- Depth reads as directional light on folded paper (a soft offset shadow, brighter edge toward the light) in light mode; dark mode swaps the shadow for a faint crease-highlight border, since shadows don't read on a dark ground.
- Poppins carries all text sitewide, loaded via Google Fonts CDN — the one new dependency this pass adds.
- One authored motion moment: the home hero's staggered fade-up entrance. Nothing else animates on load.

## Colors

One functional accent, three decorative-only hues, and a light/dark pair of neutrals that swap jobs between modes — verified against real contrast math, not eyeballed.

### Primary accent
- **Coral** (`#FF6B6B`): the system's one interactive accent — button fills, focus rings, borders on source chips and the beta mark. On light backgrounds, Coral is a **fill**, never text (2.7:1 on Paper — fails body-text contrast). In dark mode it doubles as text/links directly on Ink (6.3:1 — passes).
- **Coral Ink** (`#B34B4B`, light mode only): a darkened Coral used wherever the accent needs to sit as text or a border directly on Paper (5.0:1) — source-chip labels and links in light mode.
- **Coral Light** (`#ff8a8a`): a lightened Coral used only as the highlight end of the Facet Panel's front-plane gradient (see Components) — decorative shading within the one accent's own tonal range, not a second hue.

### Neutrals (swap jobs between modes)
- **Paper** (`#FAFAFA`): light-mode page ground. **Ink** (`#1A1A1A`): light-mode primary text; dark-mode page ground.
- **Steel** (`#4A4A4A`): light-mode secondary text (8.5:1 on Paper) and dark-mode decorative border/divider tone.
- **Fold Shadow** (`#B0B0B0`): light-mode decorative border/divider tone and dark-mode secondary text (8.0:1 on Ink).

### Decorative only — never carries text or meaning
- **Sky** (`#87CEEB`), **Sage** (`#A8D5BA`), **Warm Crease** (`#F0C987`): appear exclusively as thin crease-lines inside the hero's tessellation texture, at low opacity. Never a fill, never text, never a border on an interactive element.

### Named Rules
**The One Accent Rule.** Coral (or Coral Ink in light mode) is the only functional/interactive color across the entire site. Sky, Sage, and Warm Crease are decorative-only and confined to the hero's crease texture — if a new element wants emphasis, it earns Coral or it stays neutral.
**The Neutral Swap Rule.** Steel and Fold Shadow trade jobs between modes rather than each owning a single fixed role: Steel is text in light / border in dark, Fold Shadow is border in light / text in dark. This reuses two tones instead of inventing four.
**The Crease, Not Fill Rule.** Sky, Sage, and Warm Crease render only as thin diagonal hairlines (the tessellation device, see Elevation & Depth), never as solid filled shapes — that keeps the "folded paper catching light" logic honest instead of turning into arbitrary pastel decoration.

## Typography

**Font:** Poppins (400/500/600/700), loaded from Google Fonts on every page.
**Fallback stack:** `Poppins, system-ui, sans-serif`.
**Mono:** unchanged — `ui-monospace, "SF Mono", "Cascadia Code", "Roboto Mono", monospace`, kept for code blocks only. This pass deliberately did not add a second webfont (e.g. JetBrains Mono, part of the original template) to avoid a dependency the brief didn't ask for.
**Deliberately one family.** Poppins is the only typeface across the site — hierarchy comes from the weight/size contrast in the scale below (700 at 4rem down to 500 at 0.875rem), not from pairing a second display face.

### Hierarchy
- **Hero** (700, `clamp(2.5rem, 5vw, 4rem)`): the home page's one hero headline.
- **H1** (700, 2.25rem): the page-level heading on every restrained-tier page (workspace name on ask/conversations/files, "Workspaces", "Log In", "Register", "About", "Beta info", "New Workspace") — one step down from the landing Hero, not the same scale.
- **H2** (600, 1.5rem): the "What is RAG?" / "Workspaces" feature-row headings on the home page.
- **H2 Operate** (600, 1.125rem): sub-headings on restrained-tier pages ("Past conversations", "Files") — one step below H1 Operate, not a second unrelated scale.
- **Body** (400, 1rem/1.6): all running prose sitewide.
- **Body Large** (400, 1.125rem/1.6): the hero's intro line only — one deliberate size step up, not a second scale.
- **Label** (500, 0.875rem): buttons, nav links, source-chip labels, the beta mark, form labels.

## Layout

**One page shell, sitewide.** Every page shares the same outer frame: `max-width: 72rem`, centered, `padding: 0 1.5rem 4rem`. Nav and footer always sit flush within this shell, at the same width and position on every page — this was a deliberate fix after an early pass shipped three different container widths (72rem home, 46rem ask, 40rem everywhere else), which made the site feel like it was switching layouts as you navigated.

**Home page:** within the shared shell, the hero is a split-screen (headline + intro + primary CTA on one side, a CSS-drawn folded-paper illustration on the other), collapsing to a single stacked column below 768px. The two existing content sections ("What is RAG?", "Workspaces") run as zig-zag alternating rows — text and a decorative facet panel swap sides each row — never a 3-equal-column grid. Body copy is capped at 70ch per line. Section vertical rhythm: `clamp(3rem, 6vw, 5rem)`.

**Every other page:** within the same shared shell, actual content (headings, forms, lists, the ask page's exchange log) is capped to a comfortable 46rem reading measure and left-aligned — the same principle the home page already applies to its own hero/feature paragraphs (capped at 42ch/70ch) rather than letting prose stretch the full shell width. This includes list pages (Workspaces, Past conversations), form pages (Log In, Register, New Workspace), prose pages (About, Beta info), and the table-based Files manager.

**Page hero echo.** Every restrained-tier page now opens with a small echo of the home hero's own h1 → intro → CTA rhythm: a heading, one sentence of `.page-intro` context, then a `.page-actions` row of one or two buttons carrying the page's primary next step (Workspaces → "Create a new workspace", Ask → "See past conversations" (plus "New question" once a conversation is loaded), Past conversations → "Ask a new question", Files → "Ask a new question"). This keeps every page legible on its own, without a nav trail, the same way the home hero orients a first-time visitor.

This echo also borrows two concrete values from the home hero rather than only its rhythm: `clamp(3rem, 6vw, 5rem)` of breathing room between nav and heading (was previously flush, feeling cramped next to the home page), and the `h1` typography token (2.25rem/700) for the heading itself, replacing the smaller `h1-operate` (1.5rem/600) that every restrained page used before. This does not adopt the hero's crease-grid texture, entrance motion, or split-screen layout — those stay exclusive to the home page's full intensity.

Spacing scale (shared, unchanged): `0.25rem` / `0.5rem` / `1rem` / `1.5rem` / `2rem`.

## Elevation & Depth

Depth reads as **directional light on paper**, not generic elevation. Light mode: a soft offset shadow (`0 4px 16px rgba(26,26,26,0.08)`), always with both an offset and a blur — never a flat colored halo. Dark mode: shadows don't read against a near-black ground, so depth becomes a faint 1px highlight border (`rgba(176,176,176,0.15)`) on the surface's light-facing edge instead — a crease catching light, not a shadow.

The hero's background texture (home page only) is a **crease grid**: two crossing sets of 1px diagonal hairlines (±60°) in Sky, Sage, and Warm Crease at 6–8% opacity, evoking origami fold lines rather than filled tessellated shapes. This texture never appears on any restrained-tier page.

### Named Rules
**The Crease Light Rule.** Every faceted surface implies one light source; light mode expresses it as an offset+blur shadow, dark mode as a highlight border — never both, and never a shadow substituting for the fold-cut shape (they're independent devices).

## Shapes

Base corner radius is `0` everywhere — Origami has no rounded corners at all. The signature device is the **fold cut**: a single clipped corner via `clip-path` polygon (`shapes.cut-sm` for buttons and chips, `shapes.cut-lg` / `shapes.cut-lg-mirror` for larger facet surfaces), always the top-right corner (or its mirror on the mid facet plane), always the same size within a given component scale. Reserved for actionable/referenced elements only: primary and secondary buttons, source chips, the beta mark, and (home page only) the decorative facet panels. Entry containers, list rows, table rows, the ask input, and nav stay plain rectangles.

### Named Rules
**The Cut Corner Rule.** The fold cut marks something you can act on or follow — a button, a link-chip, a citation. It never decorates a passive container (an entry block, a list row, a paragraph, the page shell). If every element has the cut, it stops being a signature and becomes wallpaper.

## Components

### Button (Primary)
- Coral fill, Ink text (6.3:1), fold-cut top-right corner (`shapes.cut-sm`), weight 600 label type.
- Used for the one primary action on a page: the home hero's CTA, and every form's submit button (Log in, Register, Create workspace, Upload).
- Hover: 8% darken + the light-mode offset shadow strengthens; active: -1px translate, tactile press. No outer glow.

### Button (Secondary / Ghost)
- Transparent fill, 1px Fold Shadow border, same fold-cut corner, Ink text. Hover: border and text shift to Coral.
- Used for utility actions that shouldn't compete with a page's one primary action: Edit, Save, Cancel, Delete, Refresh, Open, and "See past conversations" once the ask page already shows a "New question" primary button.

### Source Chip (ask page)
- Coral Ink (light) / Coral (dark) text and border, fold-cut corner, real anchor link to its source — never a decorative badge.
- Hover/focus: fills with the accent, text flips to Paper/Ink for contrast.

### Beta Mark
- A fold-cut rectangle, 2px Coral border, Coral text, uppercase Label type — the one badge/status marker sitewide.
- Interactive: it's a real link (to the Beta info page), not decorative text. Hover/focus fills with the accent, text flips to Ink for contrast — the same "fills with the accent" idiom as the Source Chip, since visually it's already an accent-bordered chip rather than a ghost button.

### Theme Toggle
- An icon-only `.origami-button-secondary` (ghost button, same fold-cut corner) in the header, showing a vendored Lucide sun/moon SVG.
- Shows the *destination* theme, not the current one: moon while in light mode ("switch to dark"), sun while in dark mode ("switch to light"). The accessible label follows the same destination framing.
- Persists the explicit choice in `localStorage`, overriding the OS's `prefers-color-scheme` default; with no stored choice, OS preference governs as before.

### Facet Panel (home page only)
- A CSS-drawn folded-paper illustration: three overlapping fold-cut polygons in a clear tonal progression (a neutral back plane, a muted-accent mid plane with a mirrored cut, a bold-accent front plane with the smallest, boldest cut), each with its own gradient so the planes read as distinct surfaces catching light differently rather than one flat tinted rectangle. Used beside the hero headline and inside each zig-zag row's panel. Decorative, not interactive.

### Text Input
- Label above input (per the original template's own guidance): 1px Fold Shadow border, no radius, 2px Coral focus ring with 2px offset, no floating labels. Used on Log In, Register, New Workspace, and the file-upload/rename forms.
- The ask page's own input is a variant of this component, styled instead as a ruled blank line (bottom border only, no box) to match its "next line in the log" metaphor — see the Ask Input entry below.

### Ask Input (ask page only)
- Styled as the next ruled blank line in the log: no visible input chrome beyond a bottom rule, a coral-filled fold-cut "Ask" button to its right.

### Page Actions (every restrained page)
- A `.page-actions` row directly below the page's `.page-intro` sentence, holding the page's primary next step as one or two of the existing Button components — never a new button style of its own.
- One button: the sole action is styled Primary (e.g. Workspaces' "Create a new workspace", the blank ask page's "See past conversations").
- Two buttons: the forward action (e.g. "New question") is Primary; the alternate action (e.g. "See past conversations") drops to Secondary so the row still reads as one primary choice, not two competing CTAs.

### List Row (Workspaces, Past conversations)
- A plain rectangle row (no fold cut — a passive container) with a bottom hairline divider; the row's link is Ink, weight 600 (workspaces) or 500 (conversations), shifting to Coral on hover — the only accent use in an otherwise neutral list.

## Do's and Don'ts

### Do:
- **Do** keep Coral (or Coral Ink in light mode) as the only functional accent sitewide.
- **Do** reserve the fold-cut corner for actionable/referenced elements only — buttons, source chips, the beta mark.
- **Do** keep the crease-grid tessellation and hero entrance motion exclusive to the home page.
- **Do** verify any new text/background pairing against real contrast math before shipping — Coral itself fails as light-mode text (2.7:1); Coral Ink exists specifically to fix that.

### Don't:
- **Don't** add a second functional hue. Sky/Sage/Warm Crease are decorative-only, confined to the crease-grid texture.
- **Don't** put a fold cut on a passive container (entry blocks, list rows, table rows, the input field, nav) — it stops being a signature the moment it's everywhere.
- **Don't** use a conventional box-shadow in dark mode — the dark-mode depth device is a highlight border, not a shadow.
- **Don't** add a second webfont beyond Poppins without a deliberate follow-up decision.
- **Don't** reintroduce a bare/unstyled baseline — every page now carries `body.origami-world`; a new page should be built against this system from the start, not left unstyled "for now".
