## MODIFIED Requirements

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
