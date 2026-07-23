## MODIFIED Requirements

### Requirement: The frontend attaches the stored token to API requests
The system SHALL provide pages at `/register` and `/login` that submit
credentials to the registration/login endpoints and store the returned
token in `sessionStorage`, and SHALL attach that token as an
`Authorization: Bearer <token>` header on subsequent same-origin API
requests for the lifetime of the browser tab, via a single shared
request helper used by every page and form, without requiring each
page to wire this up individually.

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
