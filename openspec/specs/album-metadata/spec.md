## Purpose
Define how the app lists iCloud Photos albums and exposes album metadata needed for selecting local photo organization targets.

## Requirements

### Requirement: Album list is fetched from iCloud metadata
The system SHALL provide an API endpoint that returns the user's iCloud Photos albums using iCloud metadata rather than local folder discovery.

#### Scenario: Authenticated user requests albums
- **WHEN** an authenticated user requests the album list
- **THEN** the response contains an `albums` array
- **THEN** each album includes `id`, `name`, `asset_count`, and `folder_name`

#### Scenario: Unauthenticated user requests albums
- **WHEN** an unauthenticated user requests the album list
- **THEN** the API returns a standard error response with a `not_authenticated` error code

### Requirement: Album folder names are sanitized
The system SHALL expose a filesystem-safe folder name for each album.

#### Scenario: Album name contains invalid Windows path characters
- **WHEN** an album name contains `/`, `\\`, `:`, `*`, `?`, `"`, `<`, `>`, or `|`
- **THEN** those characters are replaced with `_` in the album folder name

#### Scenario: Album name is empty after sanitization
- **WHEN** an album name is empty after trimming invalid trailing or leading characters
- **THEN** the album folder name is `Unnamed Album`

#### Scenario: Album folder name is too long
- **WHEN** the sanitized album folder name exceeds 200 characters
- **THEN** the folder name is truncated to 200 characters

### Requirement: Album listing is lightweight
The system SHALL list albums without iterating every asset solely to display the album picker.

#### Scenario: User opens album picker
- **WHEN** the frontend requests albums for display
- **THEN** the backend returns album names and counts without syncing per-file metadata for every album

### Requirement: pyicloud album iteration uses supported APIs
The system SHALL iterate the iCloud Photos album container directly instead of treating it as a dictionary.

#### Scenario: Album container is processed
- **WHEN** the backend reads `photos.albums`
- **THEN** it iterates the album container directly
- **THEN** it does not require a `.values()` method on the album container
