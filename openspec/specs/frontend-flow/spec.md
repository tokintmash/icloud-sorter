## Purpose
Define the frontend application flow and how the React UI uses the backend sorter API contract.

## Requirements

### Requirement: Frontend uses the backend API contract
The frontend SHALL use typed API shapes that match the backend Pydantic response models for the sorter API.

#### Scenario: Frontend calls API endpoints
- **WHEN** the frontend sends or receives sorter API data
- **THEN** TypeScript request and response types match the backend schema field names and value types

### Requirement: Unauthenticated users enter through authentication
The frontend SHALL route users without an authenticated session to the Apple ID authentication flow.

#### Scenario: User is unauthenticated
- **WHEN** the app determines there is no authenticated backend session
- **THEN** the frontend shows the authentication screen

### Requirement: Authenticated users can select albums to sort
The frontend SHALL show an album picker after authentication.

#### Scenario: User is authenticated
- **WHEN** the app determines the backend session is authenticated
- **THEN** the frontend can show the album selection interface
- **THEN** the user can select one or more albums for sorting

### Requirement: Sorting users can view progress
The frontend SHALL show sort progress after a sort is started.

#### Scenario: User starts sorting
- **WHEN** the user starts sorting selected albums
- **THEN** the frontend shows progress based on SSE events from the backend
- **THEN** the frontend displays overall progress, current file or album, failures, and completion state

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
