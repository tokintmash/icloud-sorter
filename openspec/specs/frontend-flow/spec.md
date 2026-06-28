## Purpose
Define the frontend application flow and how the React UI uses the backend sorter API contract.

## Requirements

### Requirement: Frontend uses the backend API contract
The frontend SHALL use typed API shapes that match the backend Pydantic response models for the sorter API.

#### Scenario: Frontend calls API endpoints
- **WHEN** the frontend sends or receives sorter API data
- **THEN** TypeScript request and response types match the backend schema field names and value types

### Requirement: Unauthenticated users enter through authentication
The frontend SHALL route users without an authenticated session to the consent and Apple ID authentication flow.

#### Scenario: User is unauthenticated and has not accepted current consent
- **WHEN** the app determines there is no authenticated backend session
- **AND** the current consent version has not been accepted locally
- **THEN** the frontend shows the consent screen before the authentication screen

#### Scenario: User is unauthenticated and has accepted current consent
- **WHEN** the app determines there is no authenticated backend session
- **AND** the current consent version has been accepted locally
- **THEN** the frontend shows the authentication screen

#### Scenario: User accepts consent before authentication
- **WHEN** an unauthenticated user accepts the current consent statement
- **THEN** the frontend records consent locally
- **THEN** the frontend shows the authentication screen

### Requirement: Authenticated users can select albums to sort
The frontend SHALL show an album picker after authentication.

#### Scenario: User is authenticated
- **WHEN** the app determines the backend session is authenticated
- **THEN** the frontend can show the album selection interface
- **THEN** the user can select one or more albums for sorting

### Requirement: Sorting users can view progress
The frontend SHALL show sort progress inline within the album selection interface after a sort is started.

#### Scenario: User starts sorting
- **WHEN** the user starts sorting selected albums from the album selection interface
- **THEN** the frontend remains on the album selection interface
- **THEN** the frontend shows progress based on SSE events from the backend near the sort action
- **THEN** the frontend displays overall progress, current file or album, failures, and completion state

#### Scenario: Sort reaches terminal state
- **WHEN** the inline sort progress receives a terminal completion or error state
- **THEN** the frontend keeps the terminal result visible in the album selection interface
- **THEN** the frontend provides an action to dismiss the terminal result and return to normal album selection controls

### Requirement: Settings are accessible separately from the main flow
The frontend SHALL provide access to settings without replacing the authentication and sorting API contract.

#### Scenario: User opens settings
- **WHEN** the user opens settings
- **THEN** the frontend allows viewing and updating the iCloud Photos folder path
- **THEN** the frontend reflects supported backend settings fields

### Requirement: Development API requests are proxied
The frontend SHALL call `/api/*` paths so Vite development can proxy requests to the backend.

#### Scenario: Frontend runs in Vite development mode
- **WHEN** the frontend calls an API endpoint
- **THEN** the request path begins with `/api/`

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
