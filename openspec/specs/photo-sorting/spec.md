## Purpose
Define how selected iCloud Photos albums are organized by moving or copying existing local files into album-named folders.

## Requirements

### Requirement: Sorting starts for selected albums
The system SHALL provide an API endpoint that starts sorting for an explicit list of selected album IDs.

#### Scenario: Sort starts successfully
- **WHEN** the user starts sorting with one or more selected album IDs
- **THEN** the backend syncs per-file metadata for the selected albums
- **THEN** the backend starts the sorting operation
- **THEN** the response includes `total_files`

#### Scenario: Sort is already running
- **WHEN** the user starts a sort while another sort is active
- **THEN** the API returns a standard error response with a `sort_in_progress` error code

### Requirement: Files are moved within the configured iCloud Photos folder
The system SHALL organize photos by moving existing local files into album-named subfolders inside the configured iCloud Photos folder.

#### Scenario: Matching local file is found
- **WHEN** an album file has a matching local file in the configured iCloud Photos folder
- **THEN** the sorter moves the local file into the album folder
- **THEN** the file status is recorded as `sorted`

#### Scenario: Local file is not found
- **WHEN** an album file does not have a matching local file
- **THEN** the sorter records the file status as `failed`
- **THEN** the sorter records an error explaining that the file was not found
- **THEN** the sorter continues processing remaining files

### Requirement: Filename matching is case-insensitive
The system SHALL match iCloud asset filenames to local files without requiring the filename casing to be identical.

#### Scenario: Filename case differs locally
- **WHEN** iCloud metadata contains `IMG_1234.HEIC`
- **AND** the local file is named `IMG_1234.heic`
- **THEN** the sorter treats the local file as a match

### Requirement: Filename collisions are handled safely
The system SHALL avoid overwriting an existing file when moving a file into an album folder.

#### Scenario: Target filename already exists
- **WHEN** the target album folder already contains a file with the same name
- **THEN** the sorter appends a sequence suffix such as ` (2)` before the extension
- **THEN** the moved file preserves its original extension

### Requirement: Cross-album duplicates follow configured handling
The system SHALL handle files that belong to multiple selected albums according to the configured duplicate handling mode.

#### Scenario: Duplicate handling is move-only
- **WHEN** duplicate handling is configured as `move_only`
- **AND** a file appears in more than one selected album
- **THEN** the sorter moves the file for the first processed album
- **THEN** subsequent duplicate occurrences are skipped or treated as already handled without duplicating the file

#### Scenario: Duplicate handling is copy-to-each
- **WHEN** duplicate handling is configured as `copy_to_each`
- **AND** a file appears in more than one selected album
- **THEN** the sorter preserves a copy in each selected album folder where the file belongs

### Requirement: Sorting errors do not stop the whole operation
The system SHALL continue sorting remaining files when an individual file fails.

#### Scenario: One file fails during sorting
- **WHEN** a file fails because it is missing or cannot be moved
- **THEN** the failure is recorded for that file
- **THEN** the sorter continues processing the next file
