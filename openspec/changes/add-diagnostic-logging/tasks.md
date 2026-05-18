## 1. Logging Configuration

- [x] 1.1 Add a backend logging configuration module using stdlib logging and a rotating file handler.
- [x] 1.2 Add app config constants for log directory, log file path, default log level, rotation size, and backup count.
- [x] 1.3 Configure logging idempotently during backend startup so direct Python, uvicorn import, and desktop launch paths share the same behavior.
- [x] 1.4 Add explicit debug opt-in through an environment variable or equivalent non-UI mechanism.

## 2. Diagnostic Coverage

- [x] 2.1 Add `INFO` startup and initialization logs that confirm logging setup and database initialization without exposing secrets.
- [x] 2.2 Add concise authentication outcome logs that do not include passwords, 2FA codes, cookies, tokens, or raw auth responses.
- [ ] 2.3 Add concise album metadata logs for fetch/sync start, completion counts, warnings, and exceptions without raw iCloud responses.
- [ ] 2.4 Add concise sort logs for start, completion, aggregate counts, warnings, and fatal errors without default per-file logging.
- [ ] 2.5 Add settings/state warnings where load/save or initialization failures are currently swallowed or hard to diagnose.

## 3. Tests and Verification

- [ ] 3.1 Add tests that logging setup creates the log directory/file handler and is idempotent.
- [ ] 3.2 Add tests that default logging excludes `DEBUG` records and explicit debug opt-in includes them.
- [ ] 3.3 Add tests or assertions covering rotation configuration limits.
- [ ] 3.4 Add targeted tests or review fixtures to confirm authentication secrets and 2FA codes are not logged.
- [ ] 3.5 Run backend tests with `./venv/Scripts/python.exe -m pytest`.
- [ ] 3.6 Run frontend build with `cd frontend && npm run build` if frontend-affecting files changed.
