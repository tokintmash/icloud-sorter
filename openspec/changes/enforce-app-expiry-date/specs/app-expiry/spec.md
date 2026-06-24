## ADDED Requirements

### Requirement: Stamped builds expose expiry status
The system SHALL expose whether the running build is expiry-controlled and, for expiry-controlled builds, the computed expiry date.

#### Scenario: Development build has no stamp
- **WHEN** the running build has no expiry stamp
- **THEN** the expiry status reports that the build is not expiry-controlled
- **THEN** the expiry status reports that the build is not expired

#### Scenario: Stamped build has not expired
- **WHEN** the running build has an expiry stamp
- **AND** the current date is before the computed expiry date
- **THEN** the expiry status reports that the build is expiry-controlled
- **THEN** the expiry status reports the computed expiry date
- **THEN** the expiry status reports that the build is not expired

### Requirement: Expired stamped builds are blocked
The system SHALL prevent protected app functionality after an expiry-controlled build reaches its computed expiry date.

#### Scenario: Current date reaches expiry date
- **WHEN** the running build has an expiry stamp
- **AND** the current date is on or after the computed expiry date
- **THEN** the expiry status reports that the build is expired
- **THEN** protected app API endpoints are blocked

#### Scenario: Protected API request is made after expiry
- **WHEN** a client calls a protected app API endpoint after the running build has expired
- **THEN** the backend rejects the request before performing the protected operation
- **THEN** the response uses the standard expired-app error

#### Scenario: Expiry is reached during active sorting
- **WHEN** a sort operation is already active for an expiry-controlled build
- **AND** the current date reaches the computed expiry date
- **THEN** the sorter stops before processing another file
- **THEN** the sorter records a terminal expiry error state
- **THEN** no additional files are moved or copied after the expiry check fails

### Requirement: Expiry status remains available after expiry
The system SHALL keep non-functional status and shutdown paths available after expiry so users can understand the block and exit the app.

#### Scenario: Client checks expiry after expiry
- **WHEN** a client calls the app expiry status endpoint after the running build has expired
- **THEN** the backend returns the expiry status response
- **THEN** the backend does not require authentication for the status response

#### Scenario: Static frontend is loaded after expiry
- **WHEN** a user opens the app after the running build has expired
- **THEN** the frontend assets can still load
- **THEN** the app can display an expiration message instead of functional app screens

#### Scenario: Health is checked after expiry
- **WHEN** a client calls the app health endpoint after the running build has expired
- **THEN** the backend returns the health response
- **THEN** the backend does not perform protected app functionality for the health response

#### Scenario: Desktop quit is requested after expiry
- **WHEN** a client calls the app quit endpoint after the running build has expired
- **THEN** the backend allows the quit request to be handled
- **THEN** the backend does not require app functionality to be unexpired for shutdown

### Requirement: Time lookup failures do not disable expired enforcement
The system SHALL NOT treat a remote time lookup failure as proof that an expiry-controlled build is still valid.

#### Scenario: Remote time lookup fails after local expiry date
- **WHEN** the running build has an expiry stamp
- **AND** remote time lookup is unavailable
- **AND** the local UTC date is on or after the computed expiry date
- **THEN** the expiry status reports that the build is expired
- **THEN** protected app API endpoints are blocked
