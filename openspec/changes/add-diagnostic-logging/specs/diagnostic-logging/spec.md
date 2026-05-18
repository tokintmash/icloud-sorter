## ADDED Requirements

### Requirement: Backend diagnostics are persisted locally
The system SHALL write backend diagnostic logs to a local file under the user's app state directory.

#### Scenario: Application starts with logging configured
- **WHEN** the backend application starts
- **THEN** diagnostic logs are written under `~/.icloud-sorter/logs/`
- **THEN** log files are stored in a user-writable location rather than the installer-managed application directory

#### Scenario: Packaged desktop app encounters backend errors
- **WHEN** the packaged desktop application redirects standard output or standard error away from the user
- **THEN** backend diagnostic logs remain available in the local log file

### Requirement: Diagnostic logs are bounded
The system SHALL rotate diagnostic log files so logs do not grow without bound.

#### Scenario: Log file reaches the rotation limit
- **WHEN** the active diagnostic log reaches the configured rotation size
- **THEN** the system rotates to a new active log file
- **THEN** the system retains no more than the configured number of backup log files

### Requirement: Default logging uses INFO level
The system SHALL use `INFO` as the default diagnostic logging level.

#### Scenario: Normal operation is logged
- **WHEN** the app performs major operations such as startup, authentication, album fetching, settings access, or sorting
- **THEN** the logs include concise operation summaries at `INFO` level or higher

#### Scenario: Unexpected backend error occurs
- **WHEN** the backend records an unexpected exception
- **THEN** the logs include the exception details and stack trace at `ERROR` level or higher

### Requirement: Debug logging requires explicit opt-in
The system SHALL NOT enable `DEBUG` diagnostic logging unless the user or developer explicitly opts in.

#### Scenario: App starts without debug opt-in
- **WHEN** no debug logging opt-in is configured
- **THEN** `DEBUG` log records are not written to the diagnostic log file

#### Scenario: Debug logging is explicitly enabled
- **WHEN** debug logging opt-in is configured
- **THEN** the diagnostic log level includes `DEBUG` records

### Requirement: Logs protect sensitive information
The system SHALL NOT write secrets or authentication material to diagnostic logs at any log level.

#### Scenario: Authentication is logged
- **WHEN** login or two-factor authentication operations are logged
- **THEN** passwords, 2FA codes, cookies, session tokens, and raw authentication responses are not written to the logs

#### Scenario: iCloud API error is logged
- **WHEN** an iCloud API operation fails
- **THEN** raw iCloud API responses and authentication material are not written to the logs

### Requirement: Default logs avoid photo-level detail
The system SHALL avoid writing high-volume photo-level or asset-level details to default `INFO` logs.

#### Scenario: Sort processes files
- **WHEN** a sort operation runs at the default log level
- **THEN** the diagnostic logs include sort start, completion, count, warning, and fatal error summaries
- **THEN** the diagnostic logs do not include a record for every processed photo file

#### Scenario: Per-file failures occur
- **WHEN** individual files fail during sorting
- **THEN** user-facing progress and persisted sort state remain the primary source for per-file failure details
- **THEN** default diagnostic logs may include aggregate failure counts or warnings
