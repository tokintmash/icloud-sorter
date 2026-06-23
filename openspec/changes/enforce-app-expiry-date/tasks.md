## 1. Backend Expiry Enforcement

- [ ] 1.1 Refactor `backend/beta.py` so stamped builds compute expiry deterministically and fall back to local UTC date when remote time lookup fails.
- [ ] 1.2 Add a backend expiry guard for protected API routes using an allowlist for expiry status, health, quit, and static frontend delivery.
- [ ] 1.3 Return HTTP `403` with the standard `{ error, message }` response, `error: "app_expired"`, and message `This beta has expired. Contact the author of the app to get an up-to-date version.` when an expired build blocks a protected API request.
- [ ] 1.4 Add expiry checks to active sorting so the sorter stops before processing another file when expiry is reached and records a terminal `app_expired` error state.
- [ ] 1.5 Emit a terminal SSE progress event with status `error`, expiry code `app_expired`, and message `This beta has expired. Contact the author of the app to get an up-to-date version.` when expiry stops an active sort.
- [ ] 1.6 Add backend tests for unstamped development builds, active stamped builds, expired stamped builds, and remote-time-failure fallback behavior.
- [ ] 1.7 Add backend tests proving expired builds block representative protected routes for auth, albums, sort start, and settings while leaving expiry status, health, and quit available.
- [ ] 1.8 Add backend tests proving a sort that crosses the expiry date stops before processing additional files and emits/records terminal expiry progress.

## 2. Frontend Expiry Flow

- [ ] 2.1 Update frontend API error typing/handling so `app_expired` is recognized as a standard application error.
- [ ] 2.2 Ensure app initialization routes expired builds to the expiration screen with message `This beta has expired. Contact the author of the app to get an up-to-date version.` before consent, authentication, album selection, sorting, or settings.
- [ ] 2.3 Handle `app_expired` from protected API calls by stopping the current flow and showing the expiration screen with message `This beta has expired. Contact the author of the app to get an up-to-date version.`
- [ ] 2.4 Handle sort progress EventSource failures by checking expiry status and showing the expiration screen when the backend reports the build is expired.
- [ ] 2.5 Add or update frontend tests for initial expired status, active build routing, protected API `app_expired` handling, and EventSource expiry fallback.

## 3. Verification

- [ ] 3.1 Run `.\venv\Scripts\python.exe -m pytest` and fix failures.
- [ ] 3.2 Run `cd frontend && npm run build` and fix failures.
- [ ] 3.3 Manually review that `/api/app/beta` remains accessible after expiry and protected API endpoints no longer perform work.
