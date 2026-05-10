## ADDED Requirements

### Requirement: Consent screen is shown before sign-in
The system SHALL show a data access consent screen before the Apple ID login form when the user has not previously accepted the current consent version on the device/browser.

#### Scenario: New unauthenticated user opens the app
- **WHEN** an unauthenticated user opens the app without accepted local consent
- **THEN** the app shows the consent screen instead of the Apple ID login form

#### Scenario: User accepts consent
- **WHEN** the user accepts the consent statement
- **THEN** the app records the accepted consent locally and shows the Apple ID login form

### Requirement: Consent copy explains required data access
The system SHALL explain that the app reads iCloud Photos metadata and accesses local iCloud Photos files before sorting.

#### Scenario: User reviews consent details
- **WHEN** the consent screen is displayed
- **THEN** the screen states that the app reads iCloud Photos metadata including album names, asset filenames, and album membership
- **THEN** the screen states that the app accesses the local iCloud Photos folder to find and move files into album folders

### Requirement: Consent copy explains transfer boundaries
The system SHALL explain that the app does not download images or videos from iCloud and does not upload anything from the computer.

#### Scenario: User reviews transfer boundaries
- **WHEN** the consent screen is displayed
- **THEN** the screen states that the app does not download images or videos from iCloud
- **THEN** the screen states that the app does not upload files or data from the computer

### Requirement: Consent copy explains credential handling
The system SHALL explain how Apple ID credentials are used for authentication.

#### Scenario: User reviews credential handling
- **WHEN** the consent screen is displayed
- **THEN** the screen states that Apple ID credentials are submitted to the app's local backend login flow
- **THEN** the screen states that Apple ID credentials are used only to sign in with Apple/iCloud through the app's iCloud authentication service
- **THEN** the screen states that the app does not store the Apple ID password

### Requirement: Previously accepted consent is remembered locally
The system SHALL remember acceptance of the current consent version in local browser storage.

#### Scenario: Returning unauthenticated user has accepted consent
- **WHEN** an unauthenticated user opens the app with accepted local consent for the current version
- **THEN** the app shows the Apple ID login form without showing the consent screen first

### Requirement: Existing blocking and authenticated flows are preserved
The system SHALL preserve beta expiration handling and authenticated session routing when adding the consent gate.

#### Scenario: Beta build is expired
- **WHEN** the app determines the beta build is expired
- **THEN** the app shows the beta expiration screen without showing the consent screen or login form

#### Scenario: Existing session is authenticated
- **WHEN** the app determines the user already has an authenticated session
- **THEN** the app shows the authenticated application UI without requiring consent first
