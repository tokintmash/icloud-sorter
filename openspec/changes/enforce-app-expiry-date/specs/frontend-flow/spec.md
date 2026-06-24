## ADDED Requirements

### Requirement: Expired builds block frontend routing
The frontend SHALL route expired builds to an expiration screen before consent, authentication, album selection, sorting, or settings are shown.

#### Scenario: Initial expiry check reports expired build
- **WHEN** the app initializes
- **AND** the backend expiry status reports that the running build is expired
- **THEN** the frontend shows the expiration screen
- **THEN** the expiration screen displays `This beta has expired. Contact the author of the app to get an up-to-date version.`
- **THEN** the frontend does not show the consent screen
- **THEN** the frontend does not show the authentication screen
- **THEN** the frontend does not show authenticated app navigation

#### Scenario: Protected API reports expired build
- **WHEN** the frontend receives the standard expired-app error from a protected API call
- **THEN** the frontend stops the current app flow
- **THEN** the frontend shows the expiration screen
- **THEN** the expiration screen displays `This beta has expired. Contact the author of the app to get an up-to-date version.`

#### Scenario: Sort progress stream is refused after expiry
- **WHEN** the frontend sort progress EventSource fails before receiving a terminal progress event
- **THEN** the frontend checks the backend expiry status
- **AND** the backend expiry status reports that the running build is expired
- **THEN** the frontend stops the current app flow
- **THEN** the frontend shows the expiration screen
- **THEN** the expiration screen displays `This beta has expired. Contact the author of the app to get an up-to-date version.`

### Requirement: Active builds keep the existing frontend flow
The frontend SHALL preserve the existing consent, authentication, album selection, sorting, and settings flow when the running build is not expired.

#### Scenario: Initial expiry check reports active build
- **WHEN** the app initializes
- **AND** the backend expiry status reports that the running build is not expired
- **THEN** the frontend continues to session detection and the existing app flow
