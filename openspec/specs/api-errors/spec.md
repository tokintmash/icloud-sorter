## Purpose
Define the standard API error response shape and stable error codes used by frontend and backend integration.

## Requirements

### Requirement: API errors use a standard response shape
The system SHALL return expected API errors using a standard JSON shape.

#### Scenario: Expected API error occurs
- **WHEN** an API endpoint returns an expected application error
- **THEN** the response body includes `error`
- **THEN** the response body includes `message`

### Requirement: Standard error codes are defined
The system SHALL use stable error codes for common failure cases.

#### Scenario: Client handles an error
- **WHEN** the backend returns a standard error response
- **THEN** the `error` value is one of the documented application error codes for known cases

### Requirement: Authentication errors have stable codes
The system SHALL distinguish authentication failure cases with specific error codes.

#### Scenario: Credentials are invalid
- **WHEN** login credentials are rejected
- **THEN** the error code is `invalid_credentials`

#### Scenario: Two-factor verification is required or fails
- **WHEN** two-factor verification is required or fails
- **THEN** the error code identifies the two-factor authentication condition

#### Scenario: Session is missing or expired
- **WHEN** an endpoint requires authentication and no valid session exists
- **THEN** the error code is `not_authenticated` or `session_expired`

### Requirement: Sort and file operation errors have stable codes
The system SHALL distinguish sorting and filesystem failure cases with specific error codes.

#### Scenario: Sort cannot start because another sort is active
- **WHEN** a sort start request conflicts with an active sort
- **THEN** the error code is `sort_in_progress`

#### Scenario: File cannot be found locally
- **WHEN** a required local file cannot be found
- **THEN** the error code is `file_not_found`

#### Scenario: File operation lacks permission
- **WHEN** the sorter lacks permission for a file operation
- **THEN** the error code is `permission_denied`

### Requirement: Unexpected errors use an internal error code
The system SHALL report unexpected server-side failures with an internal error code rather than exposing implementation details.

#### Scenario: Unexpected backend failure occurs
- **WHEN** the backend encounters an unhandled internal condition
- **THEN** the API returns a standard error response with `internal_error`
