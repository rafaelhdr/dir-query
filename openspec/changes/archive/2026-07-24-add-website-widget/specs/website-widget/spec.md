## ADDED Requirements

### Requirement: Widget script supports two embed modes
The system SHALL serve a standalone static script (`widget.js`) that,
when embedded on any third-party page via a `<script>` tag with a
`data-workspace` attribute naming an existing workspace's slug, mounts
a chat panel for that workspace in one of two modes selected by a
`data-mode` attribute on the same script tag: `widget` (the default,
used when the attribute is omitted or has an unrecognized value) or
`inline`. The same script file SHALL serve both modes — they differ
only in how the chat panel is mounted, not in how it fetches workspace
data, submits questions, or renders answers.

#### Scenario: Omitting data-mode defaults to widget mode
- **WHEN** a page includes the widget script tag with
  `data-workspace="acme-corp"` and no `data-mode`
- **THEN** the script mounts the chat panel in widget mode (a floating
  launcher, per the next requirement)

#### Scenario: An unrecognized data-mode falls back to widget mode
- **WHEN** a page includes the widget script tag with
  `data-mode="popup"` (not a recognized mode)
- **THEN** the script mounts the chat panel in widget mode

### Requirement: Widget mode renders a floating launcher on the host page
The system SHALL, in widget mode, inject a floating launcher bubble
into the host page, positioned according to a `data-position` attribute
on the script tag (e.g. `bottom-right`, `bottom-left`), defaulting to
`bottom-right` when the attribute is omitted or has an unrecognized
value. The chat panel SHALL stay hidden until the visitor clicks the
launcher.

#### Scenario: Embedding the widget on a third-party page
- **WHEN** a page includes the widget script tag with
  `data-workspace="acme-corp"` in widget mode and no `data-position`
- **THEN** a floating launcher bubble appears fixed to the bottom-right
  corner of that page, and the chat panel is not visible until the
  launcher is clicked

#### Scenario: Configuring the launcher's position
- **WHEN** a page includes the widget script tag with
  `data-workspace="acme-corp"` in widget mode and
  `data-position="bottom-left"`
- **THEN** the floating launcher bubble appears fixed to the
  bottom-left corner of that page instead

### Requirement: Inline mode renders the chat panel directly in a host-page container
The system SHALL, in inline mode, mount the chat panel directly into a
host-page container element identified by a `data-target` attribute on
the script tag (the id of an existing element on the page), with no
launcher bubble and no fixed/floating positioning. The panel SHALL be
visible immediately once mounted, and SHALL size itself to fill its
container element rather than a fixed launcher-panel size.

#### Scenario: Embedding the widget in inline mode
- **WHEN** a page includes a container element with id `qa-panel` and
  the widget script tag with `data-workspace="acme-corp"`,
  `data-mode="inline"`, and `data-target="qa-panel"`
- **THEN** the chat panel is mounted inside the `qa-panel` element,
  visible immediately, with no floating launcher bubble anywhere on
  the page

#### Scenario: Inline panel sizes to its container
- **WHEN** the inline mode's container element is resized by the host
  page's own layout
- **THEN** the chat panel fills the container's available space rather
  than rendering at a fixed size

### Requirement: Chat panel fetches workspace data and answers questions in either mode
The system SHALL, once the chat panel is mounted (immediately in
inline mode, or when the floating launcher is clicked in widget mode),
fetch and display the workspace's name and let the visitor submit
questions to that workspace, streaming the answer using the same
question-answering behavior as the workspace's own ask page. This
behavior is identical in both embed modes.

#### Scenario: Mounting the panel shows the workspace name
- **WHEN** the chat panel is mounted for a workspace named "Acme Corp",
  whether by opening the widget-mode launcher or by inline mounting
- **THEN** the chat panel displays "Acme Corp"

#### Scenario: Asking a question through the panel streams an answer
- **WHEN** a visitor submits a question in the chat panel, in either
  embed mode
- **THEN** the panel shows a loading state and then renders the
  streamed answer, the same way a question submitted on that
  workspace's own ask page would

### Requirement: Chat panel supports follow-up questions within a session, in either mode
The system SHALL retain the conversation identifier returned by the
first answered question in a mounted chat panel and include it on
subsequent questions submitted in that same session, so follow-up
questions are answered with the prior exchanges as context. The system
SHALL NOT persist this conversation identifier beyond the current page
load — reloading the host page, or reopening a widget-mode launcher
after a reload, starts a new conversation. This behavior is identical
in both embed modes.

#### Scenario: A follow-up question uses the same conversation
- **WHEN** a visitor asks a second question in the chat panel after an
  earlier question in the same session was answered, in either embed
  mode
- **THEN** the second question is submitted as part of the same
  conversation as the first

#### Scenario: Reloading the host page starts a fresh conversation
- **WHEN** a visitor reloads the host page and asks a question in the
  chat panel again, in either embed mode
- **THEN** that question starts a new conversation, independent of any
  conversation from before the reload

### Requirement: Embedded conversations are stored like any other conversation
The system SHALL record conversations and exchanges created through
either embed mode using the same storage and the same workspace
conversation history as conversations created directly on that
workspace's ask page, with no field distinguishing an embed-originated
conversation, or which embed mode it came from, from one asked directly
on the site.

#### Scenario: An embedded conversation appears in the workspace's conversation history
- **WHEN** a visitor asks a question through an embedded chat panel for
  a workspace, in either embed mode
- **THEN** that conversation appears in that workspace's "past
  conversations" list the same way a conversation started on the
  workspace's own ask page would

### Requirement: Chat panel uses a neutral visual style independent of the site's own branding
The system SHALL render the chat panel, and the widget-mode launcher,
using a minimal, neutral visual style that does not carry this site's
own branded design direction, so the embed does not visually clash
when placed on an arbitrary third-party page, in either embed mode.

#### Scenario: Panel style does not match the site's own branding
- **WHEN** the chat panel is mounted on any host page, in either embed
  mode
- **THEN** the panel (and the launcher, in widget mode) render using
  neutral colors and typography, not this site's own accent color or
  fold-cut visual motif

### Requirement: Chat panel attributes itself to Dir Query
The system SHALL display a small "Powered by Dir Query" link inside
the mounted chat panel, pointing back to this site, in either embed
mode.

#### Scenario: Attribution link is present
- **WHEN** the chat panel is mounted, in either embed mode
- **THEN** a small "Powered by Dir Query" link is visible within the
  panel

### Requirement: Workspace and question-answering endpoints accept cross-origin requests
The system SHALL allow the widget script, running on any third-party
origin, to successfully call the workspace-detail endpoint and the
ask endpoint via cross-origin requests, without requiring the calling
origin to be registered or allowlisted in advance. This applies
identically regardless of which embed mode the script is running in.

#### Scenario: Script on a third-party origin can fetch the workspace name
- **WHEN** the widget script running on a third-party origin requests
  a workspace's details, in either embed mode
- **THEN** the response is not blocked by CORS and the script receives
  the workspace's data

#### Scenario: Script on a third-party origin can ask a question
- **WHEN** the widget script running on a third-party origin submits a
  question to the ask endpoint, in either embed mode
- **THEN** the request is not blocked by CORS and the script receives
  the streamed answer
