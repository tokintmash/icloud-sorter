## 1. Backend Expiry Enforcement

- [x] 1.1 Refactor `backend/beta.py` so stamped builds compute expiry deterministically and fall back to local UTC date when remote time lookup fails.
- [x] 1.2 Add a backend expiry guard for protected API routes using an allowlist for expiry status, health, quit, and static frontend delivery.
- [x] 1.3 Return HTTP `403` with the standard `{ error, message }` response, `error: "app_expired"`, and message `This beta has expired. Contact the author of the app to get an up-to-date version.` when an expired build blocks a protected API request.
- [x] 1.4 Add expiry checks to active sorting so the sorter stops before processing another file when expiry is reached and records a terminal `app_expired` error state.
- [x] 1.5 Emit a terminal SSE progress event with status `error`, expiry code `app_expired`, and message `This beta has expired. Contact the author of the app to get an up-to-date version.` when expiry stops an active sort.
- [x] 1.6 Add backend tests for unstamped development builds, active stamped builds, expired stamped builds, and remote-time-failure fallback behavior.
- [x] 1.7 Add backend tests proving expired builds block representative protected routes for auth, albums, sort start, and settings while leaving expiry status, health, and quit available.
- [x] 1.8 Add backend tests proving a sort that crosses the expiry date stops before processing additional files and emits/records terminal expiry progress.

## 2. Frontend Expiry Flow

- [x] 2.1 Update frontend API error typing/handling so `app_expired` is recognized as a standard application error.
- [x] 2.2 Ensure app initialization routes expired builds to the expiration screen with message `This beta has expired. Contact the author of the app to get an up-to-date version.` before consent, authentication, album selection, sorting, or settings.
- [x] 2.3 Handle `app_expired` from protected API calls by stopping the current flow and showing the expiration screen with message `This beta has expired. Contact the author of the app to get an up-to-date version.`
- [x] 2.4 Handle sort progress EventSource failures by checking expiry status and showing the expiration screen when the backend reports the build is expired.
- [x] 2.5 Add or update frontend tests for initial expired status, active build routing, protected API `app_expired` handling, and EventSource expiry fallback.

## 3. Verification

- [x] 3.1 Run `.\venv\Scripts\python.exe -m pytest` and fix failures.
- [x] 3.2 Run `cd frontend && npm run build` and fix failures.
- [x] 3.3 Manually review that `/api/app/beta` remains accessible after expiry and protected API endpoints no longer perform work.
