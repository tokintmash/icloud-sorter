## Purpose
Define how clients observe a running sort operation and receive progress, current-work, error, and completion information.

## Requirements

### Requirement: Sort progress is streamed with Server-Sent Events
The system SHALL expose sort progress over an SSE endpoint rather than WebSockets.

#### Scenario: Sort is active
- **WHEN** the frontend connects to the sort progress endpoint during an active sort
- **THEN** the backend streams progress events with media type `text/event-stream`

#### Scenario: No sort is active
- **WHEN** the frontend requests sort progress while no sort operation is active and no terminal progress state is available
- **THEN** the API returns a standard error response indicating that no sort operation is active

### Requirement: Progress events include sorting counters
The system SHALL include total, completed, and failed file counters in each sort progress event.

#### Scenario: Progress event is emitted
- **WHEN** the backend emits a progress event
- **THEN** the event includes `status`
- **THEN** the event includes `total_files`
- **THEN** the event includes `completed_files`
- **THEN** the event includes `failed_files`

### Requirement: Progress events identify current work
The system SHALL include the currently processed file and album in progress events.

#### Scenario: File is being sorted
- **WHEN** the sorter is processing a file
- **THEN** the progress event includes `current_file`
- **THEN** the progress event includes `current_album`

### Requirement: Progress events include file-level errors
The system SHALL include accumulated file-level errors in progress events.

#### Scenario: A file-level error has occurred
- **WHEN** the backend emits a progress event after a file-level failure
- **THEN** the event includes an `errors` array
- **THEN** each error includes `filename`, `error`, and `album`

### Requirement: Progress stream ends on terminal status
The system SHALL end the SSE stream when the sort reaches a terminal status.

#### Scenario: Sort completes
- **WHEN** a progress event has status `complete`
- **THEN** the backend ends the SSE stream after sending the event

#### Scenario: Sort encounters a terminal error
- **WHEN** a progress event has status `error`
- **THEN** the backend ends the SSE stream after sending the event
