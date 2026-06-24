## ADDED Requirements

### Requirement: Expired app errors have a stable code
The system SHALL return HTTP `403 Forbidden` with a standard API error when an expired build blocks a protected API operation.

#### Scenario: Expired build blocks protected operation
- **WHEN** a protected API endpoint is called after the running build has expired
- **THEN** the response status is `403`
- **THEN** the response body includes `error` with value `app_expired`
- **THEN** the response body includes `message` with value `This beta has expired. Contact the author of the app to get an up-to-date version.`
