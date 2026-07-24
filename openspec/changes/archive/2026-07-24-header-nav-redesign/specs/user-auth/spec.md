## MODIFIED Requirements

### Requirement: The frontend attaches the stored token to API requests
The system SHALL provide a single combined page at `/login` containing
both the login form and the registration form, each submitting
credentials to its respective registration/login endpoint and storing the
returned token in `sessionStorage`, and SHALL attach that token as an
`Authorization: Bearer <token>` header on subsequent same-origin API
requests for the lifetime of the browser tab, via a single shared request
helper used by every page and form, without requiring each page to wire
this up individually. There SHALL NOT be a separate `/register` route —
registration is reached only via the combined `/login` page.

#### Scenario: Token persists across page navigation within a tab
- **WHEN** a user logs in and then navigates to a different page within
  the same browser tab
- **THEN** subsequent API requests from that page still include the
  stored token

#### Scenario: Token is not available in a new tab
- **WHEN** a user logs in, then opens the site in a new browser tab
- **THEN** the new tab has no stored token and behaves as logged out

#### Scenario: Logging out clears the stored token
- **WHEN** a logged-in user logs out
- **THEN** the token is removed from `sessionStorage` and subsequent
  requests from that tab are sent without an `Authorization` header

#### Scenario: Registering from the combined login page
- **WHEN** a visitor fills in the registration form on `/login` and
  submits it
- **THEN** the frontend posts to the registration endpoint and, on
  success, stores the returned token the same way a login submission
  would

#### Scenario: Visiting the removed /register route
- **WHEN** a browser navigates directly to `/register`
- **THEN** the server returns a 404, since no page is served at that path
