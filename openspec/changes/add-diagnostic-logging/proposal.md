## Why

The app currently has a few logger calls but no centralized diagnostic logging configuration, so important failures can disappear, especially in the packaged desktop app where standard output/error may be redirected away. Local, privacy-conscious logs would make startup, authentication, iCloud API, and sorting failures diagnosable without turning the app into a verbose audit trail.

## What Changes

- Add backend diagnostic logging with a default `INFO` level and local rotating log files.
- Preserve privacy by excluding secrets and avoiding high-volume photo-level details from default logs.
- Allow `DEBUG` logging only through explicit opt-in for troubleshooting.
- Record major lifecycle and operation summaries such as startup, settings loading, authentication outcomes, album fetch summaries, sort start/completion summaries, warnings, and unexpected exceptions.
- Keep user-facing per-file sort progress and failures in the existing UI/SSE/state mechanisms rather than duplicating every detail in default logs.

## Capabilities

### New Capabilities
- `diagnostic-logging`: Local backend diagnostic logging behavior, privacy boundaries, log level expectations, and retention/rotation requirements.

### Modified Capabilities

None.

## Impact

- Backend startup and desktop launcher paths will need to configure logging consistently.
- Existing backend service logger calls can start producing persistent diagnostics once configuration exists.
- Sorting, authentication, settings, album metadata, and database initialization paths may add concise summary logs and warnings.
- No API contract changes are expected.
- No frontend UI changes are required unless a future change adds user-facing log controls.
