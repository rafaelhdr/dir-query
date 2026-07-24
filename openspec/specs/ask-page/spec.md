## Purpose

The ask page (`/w/<slug>/ask`) is where a user asks questions about a
workspace's uploaded documents. It submits the question to that
workspace's backend question-answering endpoint and displays the
returned answer.
## Requirements
### Requirement: Ask page provides a question input
The system SHALL serve a page at `/w/<slug>/ask` for an existing workspace
identified by `<slug>`, with a text input where a user can type a
question for that workspace, positioned inline in the page directly
after the most recently displayed exchange (or at the top of the page if
no exchange has been asked yet in the current conversation), so that it
moves down the page as exchanges accumulate rather than remaining fixed
in the viewport.

#### Scenario: Visiting the ask page for an existing workspace
- **WHEN** a user navigates to `/w/<slug>/ask` for a workspace that exists
- **THEN** the page loads successfully and displays a question input

#### Scenario: Input follows the latest exchange
- **WHEN** a user has already asked one or more questions in the current
  conversation on a workspace's ask page
- **THEN** the question input is positioned directly after the most
  recently displayed exchange, not fixed at the bottom of the viewport

### Requirement: Ask page submits questions to the backend and displays the answer
The system SHALL submit each question entered on a workspace's ask page
to that workspace's backend question-answering endpoint, SHALL display a
loading state for that question until the first part of the answer
arrives, SHALL progressively render the answer text as formatted Markdown
as it streams in from the backend rather than waiting for the complete
answer, and SHALL display each question together with its resulting
answer (or error) as its own exchange, stacked below any previous
exchanges in the same conversation, without limit on how many exchanges
can accumulate on the page.

#### Scenario: Submitting a question shows the answer streaming in
- **WHEN** a user types a question into the input on a workspace's ask
  page and submits it
- **THEN** the question is immediately displayed, a loading indicator is
  shown until the backend begins sending the answer, and the loading
  indicator is then replaced with the answer text progressively
  rendering as it streams in, until the complete answer and its sources
  are shown

#### Scenario: Submitting a second question appends below the first
- **WHEN** a user submits a question after an earlier question in the
  same conversation has already been answered and displayed
- **THEN** the new question and its resulting answer are displayed below
  the earlier exchange, and the earlier exchange remains visible
  unchanged

#### Scenario: Backend error is shown to the user
- **WHEN** the backend returns an error in response to a submitted
  question, whether before any answer text has streamed or partway
  through streaming
- **THEN** that exchange displays a clear error message in place of an
  answer, and earlier exchanges in the same conversation remain
  displayed unchanged

### Requirement: Ask page links to the other pages
The system SHALL provide navigation from a workspace's ask page to the
home page (`/`) and, via a tab bar shared with the workspace's upload
page, to that same workspace's upload page (`/w/<slug>/feed/upload`),
with the "Ask" tab visually marked as the selected tab.

#### Scenario: Navigating from ask to home
- **WHEN** a user clicks the "Home" navigation link on the ask page
- **THEN** the browser navigates to `/`

#### Scenario: Navigating from ask to that workspace's upload page via the tab bar
- **WHEN** a user clicks the "Upload" tab on a workspace's ask page
- **THEN** the browser navigates to that same workspace's
  `/w/<slug>/feed/upload` page

#### Scenario: Ask tab is selected on the ask page
- **WHEN** a user is on a workspace's ask page
- **THEN** the "Ask" tab in the tab bar is visually marked as selected
  and the "Upload" tab is not

### Requirement: Ask page heading shows the workspace's name
The system SHALL display the workspace's name (not a generic label) as
the `<h1>` heading on a workspace's ask page, fetched from the backend
using the slug in the URL.

#### Scenario: Workspace name appears in the heading
- **WHEN** a user navigates to `/w/<slug>/ask` for a workspace named
  "Acme Corp" (slug `acme-corp`)
- **THEN** the page's `<h1>` displays "Acme Corp"

#### Scenario: Nonexistent workspace
- **WHEN** a user navigates to `/w/<slug>/ask` for a slug that does not
  correspond to any existing workspace
- **THEN** the page indicates the workspace could not be found instead
  of displaying a workspace name

### Requirement: Bare workspace URL defaults to the ask page
The system SHALL serve the ask page, with its "Ask" tab selected, when a
user navigates to a workspace's bare URL `/w/<slug>` for an existing
workspace.

#### Scenario: Opening a workspace by its bare URL
- **WHEN** a user navigates to `/w/<slug>` for a workspace that exists
- **THEN** the ask page for that workspace loads, showing that
  workspace's name in the heading and the "Ask" tab selected

### Requirement: Ask page provides a way to start a new conversation
The system SHALL provide an action on a workspace's ask page that starts
a new, empty conversation: clearing any exchanges currently displayed and
resetting the page so the next submitted question begins a new
conversation rather than continuing the previous one.

#### Scenario: Starting a new conversation clears the current thread
- **WHEN** a user has one or more exchanges displayed on a workspace's
  ask page and selects the action to start a new conversation
- **THEN** the displayed exchanges are cleared and the next question the
  user submits begins a new conversation

### Requirement: Ask page links to that workspace's conversation history
The system SHALL provide navigation from a workspace's ask page to a
view listing that workspace's past conversations by title and date.

#### Scenario: Navigating to the conversation list
- **WHEN** a user selects the conversation history navigation on a
  workspace's ask page
- **THEN** the browser navigates to a page listing that workspace's past
  conversations

### Requirement: Ask page can reopen a past conversation
The system SHALL, when a workspace's ask page is opened for a specific
existing conversation, load and display that conversation's full
exchange history, including any exchanges with a status of failed shown
with an error indicator, with the question input positioned after the
last displayed exchange ready to continue that same conversation.

#### Scenario: Opening a past conversation from the conversation list
- **WHEN** a user selects a past conversation from that workspace's
  conversation list
- **THEN** the ask page loads showing that conversation's full exchange
  history in the order the questions were originally asked, with the
  question input positioned after the last exchange

#### Scenario: A failed exchange is shown when reopening a conversation
- **WHEN** a reopened conversation includes an exchange with a status of
  failed
- **THEN** that exchange is displayed in its original position with an
  error indicator instead of an answer

#### Scenario: Continuing a reopened conversation
- **WHEN** a user submits a new question on a reopened conversation's ask
  page
- **THEN** the new question is submitted as part of that same
  conversation and its resulting exchange is appended after the loaded
  history

