## Purpose
Define the Apple ID authentication, two-factor verification, and session-status behavior required before users can access iCloud Photos metadata.

## Requirements

### Requirement: Apple ID login is supported
The system SHALL provide an API endpoint that accepts an Apple ID and password and attempts authentication through the in-process iCloud authentication service.

#### Scenario: Login succeeds without two-factor authentication
- **WHEN** the user submits valid credentials and iCloud does not require two-factor verification
- **THEN** the login response indicates `authenticated: true`
- **THEN** the login response indicates `requires_2fa: false`

#### Scenario: Login requires two-factor authentication
- **WHEN** the user submits valid credentials and iCloud requires two-factor verification
- **THEN** the login response indicates `authenticated: false`
- **THEN** the login response indicates `requires_2fa: true`

#### Scenario: Login fails
- **WHEN** the user submits invalid credentials
- **THEN** the API returns a standard error response with an `invalid_credentials` error code

### Requirement: Two-factor verification is supported
The system SHALL provide an API endpoint that accepts a two-factor verification code after a login attempt requires it.

#### Scenario: Two-factor verification succeeds
- **WHEN** the user submits a valid two-factor code
- **THEN** the response indicates `authenticated: true`

#### Scenario: Two-factor verification fails
- **WHEN** the user submits an invalid two-factor code
- **THEN** the API returns a standard error response with a `2fa_failed` or `not_authenticated` error code

### Requirement: Session status is available
The system SHALL provide an API endpoint that reports whether the current backend iCloud session is authenticated.

#### Scenario: Session is checked
- **WHEN** the frontend requests session status
- **THEN** the response includes `authenticated`, `apple_id`, and `requires_2fa`

### Requirement: Authentication errors use the standard error shape
The system SHALL return authentication errors using the standard API error response shape.

#### Scenario: Authentication error is returned
- **WHEN** an authentication request fails
- **THEN** the response body includes `error`
- **THEN** the response body includes `message`
