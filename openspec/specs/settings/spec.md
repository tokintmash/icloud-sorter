## Purpose
Define user-configurable sorter settings, including the local iCloud Photos folder and duplicate handling behavior.

## Requirements

### Requirement: iCloud Photos folder setting is available
The system SHALL provide settings APIs for reading and updating the configured local iCloud Photos folder.

#### Scenario: Settings are read
- **WHEN** the frontend requests settings
- **THEN** the response includes `icloud_folder`

#### Scenario: iCloud Photos folder is updated
- **WHEN** the frontend updates `icloud_folder`
- **THEN** the backend persists the new folder path
- **THEN** the response includes the full updated settings object

### Requirement: Duplicate handling setting is available
The system SHALL expose the configured duplicate handling mode in settings.

#### Scenario: Duplicate handling is read
- **WHEN** the frontend requests settings
- **THEN** the response includes `duplicate_handling`
- **THEN** `duplicate_handling` is either `move_only` or `copy_to_each`

#### Scenario: Duplicate handling is updated
- **WHEN** the frontend updates `duplicate_handling` to `move_only` or `copy_to_each`
- **THEN** the backend persists the new duplicate handling mode
- **THEN** the response includes the full updated settings object

### Requirement: Settings updates are partial
The system SHALL allow settings updates that include only the fields being changed.

#### Scenario: One setting is updated
- **WHEN** the frontend sends a settings update containing only `icloud_folder`
- **THEN** the backend preserves the existing duplicate handling setting

#### Scenario: Unknown fields are not part of the contract
- **WHEN** the frontend follows the settings API contract
- **THEN** it sends only supported settings fields

### Requirement: iCloud folder discovery has manual fallback
The system SHALL allow the user to manually configure the iCloud Photos folder when automatic discovery is absent or incorrect.

#### Scenario: Default folder is wrong or unavailable
- **WHEN** the app cannot rely on a discovered iCloud Photos folder
- **THEN** the user can configure the folder path in settings
