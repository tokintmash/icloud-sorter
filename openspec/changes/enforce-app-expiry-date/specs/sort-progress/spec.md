## ADDED Requirements

### Requirement: Sort progress reports expiry as a terminal error
The system SHALL report expiry during an active sort as a terminal SSE progress error before ending the stream.

#### Scenario: Expiry occurs while progress stream is active
- **WHEN** a sort operation is active
- **AND** the running build reaches its computed expiry date
- **THEN** the backend emits a progress event with status `error`
- **THEN** the event identifies the expiry condition with error code `app_expired`
- **THEN** the event includes message `This beta has expired. Contact the author of the app to get an up-to-date version.`
- **THEN** the backend ends the SSE stream after sending the terminal event
