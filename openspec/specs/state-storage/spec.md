## Purpose
Define the local SQLite state used to track album/file metadata and per-file sorting outcomes.

## Requirements

### Requirement: Album file state is stored in SQLite
The system SHALL store album/file sort state in a local SQLite database at the application state path.

#### Scenario: Database is initialized
- **WHEN** the backend initializes state storage
- **THEN** the database contains an `album_files` table

### Requirement: Album file rows identify album membership
The system SHALL store album membership per file using album and filename fields.

#### Scenario: Album file metadata is stored
- **WHEN** selected album metadata is synced
- **THEN** each stored row includes `album_id`, `album_name`, `filename`, and `folder_name`

### Requirement: Sort status is tracked per album file
The system SHALL track sort status independently for each album/file row.

#### Scenario: File is pending
- **WHEN** a file has been synced but not successfully sorted or failed
- **THEN** its status is `pending`

#### Scenario: File is sorted
- **WHEN** a file has been moved or otherwise handled successfully for an album
- **THEN** its status is `sorted`

#### Scenario: File fails
- **WHEN** a file cannot be sorted for an album
- **THEN** its status is `failed`
- **THEN** its error field contains the failure reason

### Requirement: Album file identity is unique per album and filename
The system SHALL prevent duplicate state rows for the same album ID and filename pair.

#### Scenario: Same file metadata is synced again for an album
- **WHEN** the backend stores metadata for an album ID and filename pair that already exists
- **THEN** the existing row is updated or replaced rather than creating a duplicate row

### Requirement: State queries support status and album lookups
The system SHALL index album file state for status-based and album-based operations.

#### Scenario: Sorter looks up pending files
- **WHEN** the sorter queries files by selected albums or status
- **THEN** the database supports efficient album and status filtering
