## Context

The backend already imports Python logging in some services and records a few exceptions, but the application does not configure a durable logging destination. In development, logs may surface through uvicorn or standard error. In the packaged desktop app, `stdout` and `stderr` can be redirected to `os.devnull`, making failures difficult to diagnose after launch.

The app handles Apple authentication state, local photo paths, album names, filenames, cookies, and user filesystem state. Diagnostic logging must therefore be useful without becoming a privacy risk or a high-volume record of a user's photo library.

## Goals / Non-Goals

**Goals:**

- Configure backend logging consistently for both `python backend/app.py`, `uvicorn backend.app:app`, and the packaged desktop launcher.
- Persist diagnostic logs under the existing user-writable app state directory.
- Use `INFO` as the default level for operational summaries and unexpected failures.
- Require explicit opt-in for `DEBUG` logging.
- Keep secrets, authentication material, and high-volume photo-level details out of default logs.
- Use log rotation so diagnostics do not grow without bound.

**Non-Goals:**

- Add a frontend log viewer or settings UI for logs.
- Replace existing SSE progress, API errors, or `album_files` status/error records.
- Create a detailed audit trail of every photo/file action.
- Add remote telemetry, analytics, crash reporting, or automatic log upload.
- Introduce an external logging service or dependency.

## Decisions

### Use stdlib logging with rotating local files

Use Python's standard `logging` package with a rotating file handler writing under `~/.icloud-sorter/logs/`, for example `app.log` plus a small number of backups.

Alternatives considered:
- Console-only logging: too fragile for the packaged desktop app because output may be unavailable.
- A third-party logging package: unnecessary for the app's current needs and adds dependency/packaging surface.
- SQLite-backed logs: complicates retention and mixes operational diagnostics with application state.

### Configure logging during application startup

Logging should be configured before backend initialization work that can fail, while remaining safe if modules are imported by uvicorn. The configuration should be idempotent so repeated imports or test setup do not duplicate handlers.

Alternatives considered:
- Configure only in `desktop_launcher.py`: misses direct backend development and uvicorn entry points.
- Configure only in `backend/app.py`: may still be acceptable for backend behavior, but desktop startup failures before app import would be less visible.

### Default to `INFO`, explicitly opt in to `DEBUG`

`INFO` should record major lifecycle events and summaries: startup, shutdown intent, settings load/save issues, authentication outcome categories, album fetch counts, sort start/completion summaries, warnings, and exception stack traces.

`DEBUG` should be available only through an explicit troubleshooting mechanism such as an environment variable. It may include more detailed branch decisions, timing, path resolution, duplicate-handling decisions, and file matching diagnostics, while still excluding secrets.

Alternatives considered:
- Default to `WARNING`: safer but too sparse for diagnosing user reports where no exception occurs.
- Default to `DEBUG`: too noisy and more likely to capture personal library details by default.

### Treat privacy boundaries as requirements, not conventions

Logs must not include passwords, 2FA codes, cookies, raw session material, authentication tokens, or raw iCloud API responses. Default `INFO` logs should avoid per-file and per-asset details; those remain visible through existing user-facing progress and persisted state when needed.

Alternatives considered:
- Rely on developer judgment at each call site: too easy to regress over time.
- Redact only known secret field names: useful but insufficient because filenames, album names, and local paths can also be sensitive.

## Risks / Trade-offs

- Logs may still reveal local usernames or configured folder paths through state directory/path diagnostics -> Keep path logging concise and avoid broad directory inventories.
- Debug mode can become noisy or privacy-sensitive if overused -> Require explicit opt-in and document that debug logs are troubleshooting artifacts.
- Duplicate handlers can produce repeated log lines when uvicorn reloads or tests import the app multiple times -> Make logging setup idempotent and test it.
- Log files may grow over time -> Use rotation with bounded file size and backup count.
- Too little default detail may still make some bugs hard to diagnose -> Keep `INFO` focused on operation boundaries, counts, warnings, and exception traces, and reserve deeper correlation for opt-in `DEBUG`.

## Migration Plan

No data migration is required. The logs directory can be created lazily on startup. Existing installations should continue using the same state directory, and uninstall behavior should continue preserving user state under `~/.icloud-sorter`.

Rollback is straightforward: removing logging configuration leaves existing log files behind but does not affect app state, settings, cookies, or photo files.

## Open Questions

- Should `DEBUG` be enabled only by environment variable initially, or should a later settings UI expose a temporary troubleshooting toggle?
- What exact rotation size and backup count best balances usefulness with disk footprint?
