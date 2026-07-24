## Purpose

The user-auth capability lets a visitor register an account (email +
password) and log in, receiving a bearer token the frontend uses to
authenticate subsequent requests. It underpins optional workspace
ownership in the `workspace-management` capability: a workspace
created while authenticated is owned by that user, and only they may
edit it.
## Requirements
### Requirement: A visitor can register with email and password
The system SHALL provide an endpoint to create a new user account from
an email and password, storing the password only as a salted hash
(using the same `pgcrypto` salted-hash approach already used for
workspace passwords), and SHALL normalize the email to lowercase for
storage and all future comparisons.

#### Scenario: Successful registration
- **WHEN** a visitor submits a registration with a non-empty email and
  a non-empty password not already registered
- **THEN** a new `users` row is created with the password stored as a
  salted hash, not plaintext

#### Scenario: Email is normalized to lowercase
- **WHEN** a visitor registers with `Foo@Bar.com`
- **THEN** the stored email is `foo@bar.com`

#### Scenario: Duplicate email is rejected
- **WHEN** a visitor registers with an email that already belongs to an
  existing user (case-insensitively)
- **THEN** the backend rejects the request with a clear conflict error
  and does not create a second account

#### Scenario: Missing email or password is rejected
- **WHEN** a visitor submits registration without an email or without a
  password
- **THEN** the backend responds with a clear validation error and does
  not create an account

### Requirement: Registration automatically logs the user in
The system SHALL respond to a successful registration with the same
token response shape as login, so the visitor does not need to submit
their credentials a second time.

#### Scenario: Token issued on registration
- **WHEN** a visitor successfully registers
- **THEN** the response includes a valid bearer token for the newly
  created user, usable immediately on subsequent requests

### Requirement: A registered user can log in with email and password
The system SHALL provide an endpoint that verifies an email/password
pair against a stored user (comparing the email case-insensitively)
and, on success, issues a signed JWT bearer token valid for 18 hours.

#### Scenario: Successful login
- **WHEN** a user submits the email and password matching an existing
  account
- **THEN** the backend responds with a valid bearer token for that user

#### Scenario: Login is case-insensitive on email
- **WHEN** a user registered with `foo@bar.com` logs in with
  `Foo@Bar.com` and the correct password
- **THEN** the login succeeds

#### Scenario: Wrong password is rejected
- **WHEN** a user submits an email that exists but the wrong password
- **THEN** the backend rejects the request with a generic invalid-
  credentials error and does not indicate whether the email exists

#### Scenario: Unknown email is rejected
- **WHEN** a user submits an email with no matching account
- **THEN** the backend rejects the request with the same generic
  invalid-credentials error used for a wrong password, so the two
  cases are indistinguishable to the caller

### Requirement: Bearer tokens are short-lived and stateless
The system SHALL issue JWT bearer tokens that expire 18 hours after
issuance, SHALL verify the token's signature and expiry on every
request that requires authentication, and SHALL NOT provide a refresh
mechanism or a way to extend a token's lifetime short of logging in
again.

#### Scenario: Expired token is rejected
- **WHEN** a request is made with a bearer token issued more than 18
  hours earlier
- **THEN** the backend rejects the request as unauthenticated

#### Scenario: Tampered token is rejected
- **WHEN** a request is made with a bearer token whose signature does
  not verify against the server's signing key
- **THEN** the backend rejects the request as unauthenticated

### Requirement: Logout is client-side only
The system SHALL NOT provide server-side token revocation. A token
remains valid until its natural expiry regardless of whether the user
has logged out client-side.

#### Scenario: Token still works after client-side logout
- **WHEN** a user has logged out (cleared their locally stored token)
  but a copy of that same still-unexpired token is presented on a
  request
- **THEN** the backend accepts the request as authenticated, since no
  server-side revocation exists

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

