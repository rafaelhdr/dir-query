## ADDED Requirements

### Requirement: Ask page provides a way to generate an embeddable widget snippet
The system SHALL provide an action on a workspace's ask page, available
to any visitor, labeled "Make a widget for your website", positioned
alongside the existing conversation-history navigation. Selecting it
SHALL open a modal containing a `<script>` snippet that embeds that
workspace's chat panel (see the `website-widget` capability) on a
third-party site, built using the current page's origin and the
workspace's slug, and a button that copies that snippet to the
clipboard.

#### Scenario: Opening the widget modal
- **WHEN** a visitor selects "Make a widget for your website" on a
  workspace's ask page
- **THEN** a modal opens showing a `<script>` snippet that embeds a
  chat panel for that same workspace

#### Scenario: Copying the snippet
- **WHEN** a visitor selects the copy button inside the widget modal
- **THEN** the snippet's text is copied to the visitor's clipboard and
  the button indicates the copy succeeded

### Requirement: Widget modal lets the visitor choose between widget and inline embed modes
The system SHALL offer a choice, presented as radio buttons inside the
widget modal, between two embed modes — "Widget" (a floating launcher
bubble) and "Inline" (the chat panel rendered directly in the
embedder's own page layout) — defaulting to "Widget" when the modal is
opened. The generated `<script>` snippet SHALL reflect whichever mode
is currently selected, updating immediately when the selection changes,
without requiring the modal to be reopened.

#### Scenario: Widget mode is selected by default
- **WHEN** a visitor opens the widget modal
- **THEN** the "Widget" option is selected and the displayed snippet
  embeds the workspace in widget mode

#### Scenario: Switching to inline mode updates the snippet
- **WHEN** a visitor selects the "Inline" option in the widget modal
- **THEN** the displayed snippet updates to embed the workspace in
  inline mode instead, without closing or reopening the modal

### Requirement: Widget modal warns when the workspace has no owner
The system SHALL display a warning inside the widget modal, stating
that the widget may stop working if the workspace is later removed,
whenever the workspace has no owner. The system SHALL NOT display this
warning when the workspace has an owner.

#### Scenario: Warning shown for an ownerless workspace
- **WHEN** a visitor opens the widget modal for a workspace that has no
  owner
- **THEN** the modal displays a warning that the widget may stop
  working if the workspace is later cleaned up

#### Scenario: Warning not shown for an owned workspace
- **WHEN** a visitor opens the widget modal for a workspace that has an
  owner
- **THEN** the modal does not display that warning
