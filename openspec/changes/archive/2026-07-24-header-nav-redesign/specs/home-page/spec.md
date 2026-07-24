## MODIFIED Requirements

### Requirement: Home page discloses beta status
The system SHALL clearly indicate, via a badge in the site header shown on
every page, that the application is a beta version, and that uploaded
documents are not yet processed or searchable. The badge SHALL be a link
to the `/beta` page, where more detail is available.

#### Scenario: Beta notice is visible
- **WHEN** a user views any page of the application
- **THEN** the site header displays a visible badge stating the
  application is in beta, and uploads are not yet processed or searchable

#### Scenario: Navigating to Beta info via the badge
- **WHEN** a user clicks the Beta badge in the site header
- **THEN** the browser navigates to `/beta`
