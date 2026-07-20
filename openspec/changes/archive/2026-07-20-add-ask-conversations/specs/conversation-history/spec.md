## ADDED Requirements

### Requirement: A conversation is created automatically on its first question
The system SHALL NOT create a `Conversation` record until a user submits
the first question that belongs to it. Submitting a question without an
existing conversation to attach to SHALL create a new conversation as
part of answering that question.

#### Scenario: Asking a question with no existing conversation
- **WHEN** a user submits a question to a workspace without referencing
  an existing conversation
- **THEN** a new conversation is created for that workspace and the
  submitted question becomes its first exchange

#### Scenario: Starting a new conversation without asking anything
- **WHEN** a user starts a new conversation but does not submit any
  question
- **THEN** no conversation record is created for that workspace

### Requirement: A conversation's title is derived from its first question
The system SHALL set a newly created conversation's title from the text
of the question that created it (truncated if necessary), without
requiring the user to provide a title.

#### Scenario: Title reflects the first question
- **WHEN** a new conversation is created by a user asking "What is the
  refund policy?"
- **THEN** the conversation's title is derived from that question's text

### Requirement: Each question and answer is persisted as an exchange
The system SHALL persist every question submitted within a conversation
as an exchange record, tracking a status of pending, answered, or
failed, and SHALL record the exchange before the answer is known, so
that a question is never lost even if answering it fails.

#### Scenario: A successfully answered question is persisted
- **WHEN** a user submits a question and the backend successfully
  generates an answer
- **THEN** an exchange recording that question, its answer, and its
  sources is persisted with a status of answered

#### Scenario: A failed question is still persisted
- **WHEN** a user submits a question and the backend fails to generate an
  answer (for example, due to an LLM provider error)
- **THEN** an exchange recording that question is persisted with a status
  of failed and no answer

### Requirement: A workspace's conversations can be listed
The system SHALL provide a way to list all conversations that exist for
a given workspace, showing each conversation's title and when it was
created, ordered with the most recently active conversations first.

#### Scenario: Listing conversations for a workspace with history
- **WHEN** a user requests the list of conversations for a workspace that
  has one or more conversations
- **THEN** the system returns each conversation's title and creation
  time, most recently active first

#### Scenario: Listing conversations for a workspace with no history
- **WHEN** a user requests the list of conversations for a workspace that
  has no conversations yet
- **THEN** the system returns an empty list

### Requirement: A conversation's full history can be retrieved
The system SHALL provide a way to retrieve a single conversation's title
and its complete ordered list of exchanges, including any exchanges with
a status of failed, so that reopening a conversation shows exactly what
happened, including questions that were never successfully answered.

#### Scenario: Reopening a conversation with only answered exchanges
- **WHEN** a user requests a conversation whose exchanges were all
  answered successfully
- **THEN** the system returns the conversation's title and its exchanges
  in the order they were asked, each with its question, answer, and
  sources

#### Scenario: Reopening a conversation that includes a failed exchange
- **WHEN** a user requests a conversation that includes an exchange with
  a status of failed
- **THEN** the system returns that exchange in its place in the ordered
  history, marked as failed, with no answer

#### Scenario: Requesting a conversation that does not exist
- **WHEN** a user requests a conversation id that does not exist, or that
  belongs to a different workspace than the one specified
- **THEN** the system responds with a 404 error
