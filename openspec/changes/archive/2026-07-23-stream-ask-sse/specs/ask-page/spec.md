## MODIFIED Requirements

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
