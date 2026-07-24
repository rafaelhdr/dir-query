## MODIFIED Requirements

### Requirement: The frontend attaches the stored token to API requests
The system SHALL provide a single combined page at `/login` containing
both the login form and the registration form, each submitting
credentials to its respective registration/login endpoint and storing the
returned token in `localStorage`, and SHALL attach that token as an
`Authorization: Bearer <token>` header on subsequent same-origin API
requests for as long as the token remains stored, via a single shared
request helper used by every page and form, without requiring each page
to wire this up individually. There SHALL NOT be a separate `/register`
route — registration is reached only via the combined `/login` page.

#### Scenario: Token persists across page navigation within a tab
- **WHEN** a user logs in and then navigates to a different page within
  the same browser tab
- **THEN** subsequent API requests from that page still include the
  stored token

#### Scenario: Token is available in a new tab
- **WHEN** a user logs in, then opens the site in a new browser tab or
  window of the same browser
- **THEN** the new tab has the same stored token and behaves as logged in

#### Scenario: Logging out clears the stored token
- **WHEN** a logged-in user logs out
- **THEN** the token is removed from `localStorage` and subsequent
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

## ADDED Requirements

### Requirement: Logout is propagated to other open tabs
The system SHALL update the logged-in UI state in other open tabs of the
same browser when the stored token is removed by a logout in a different
tab, using the browser's storage-change notification, without requiring
those tabs to make a request or be reloaded first.

#### Scenario: Other tab reflects logout immediately
- **WHEN** a user is logged in in two open tabs and clicks logout in one
  of them
- **THEN** the other tab's UI updates to a logged-out state without the
  user reloading it or triggering a request in it
