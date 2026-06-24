## Context

The app currently has beta expiry plumbing in `backend/beta.py` and a frontend check in `App.tsx`. The frontend displays an expired screen when `/api/app/beta` reports `expired: true`, but protected backend endpoints remain available and the beta status function fails open if the external time API cannot be reached. That makes expiry advisory instead of enforceable.

The expiry mechanism must still allow unstamped development builds to run, and the SPA must still load far enough to tell the user that a stamped build has expired.

## Goals / Non-Goals

**Goals:**
- Make expiry enforcement backend-authoritative for stamped builds.
- Block protected API functionality once the current date is on or after the computed expiry date.
- Stop active sort work when expiry is reached, before processing additional files.
- Keep `/api/app/beta` available so the frontend can render an expired-build screen.
- Keep development builds without a beta stamp usable.
- Add tests that prove expired builds cannot authenticate, list albums, start sorting, update settings, or continue sorting after expiry is reached.

**Non-Goals:**
- Replacing beta expiry with a paid licensing system.
- Changing how iCloud authentication, album metadata, sorting, or SQLite state work beyond guarding access.
- Blocking static frontend assets or the expired-build informational screen.
- Adding a new external dependency for time lookup or licensing.

## Decisions

1. Enforce expiry in backend middleware or a shared FastAPI dependency before protected routes run.

   Rationale: Frontend-only checks can be bypassed and do not protect direct API calls. A shared backend gate avoids duplicating expiry checks across routers while keeping route handlers focused on domain behavior.

   Alternatives considered: only fix `App.tsx`, or add checks inside each route handler. Frontend-only enforcement does not satisfy the requirement that the app must not function after expiry; per-route checks are more error-prone.

2. Exempt only non-functional/status routes needed after expiry.

   Rationale: `/api/app/beta` must remain accessible so clients can discover expiry details, `/api/app/health` may remain available for process checks, and the SPA/static files must remain accessible to show the expired message. `/api/app/quit` can remain available because quitting is not app functionality and helps desktop users exit. Protected routes such as auth, albums, sort start, and settings must return an expiry error.

   Alternatives considered: block every request including static files, or allow read-only API endpoints. Blocking static files prevents the user from seeing the reason for failure; allowing read-only endpoints leaves meaningful app functionality available.

3. Return HTTP `403 Forbidden` with a standard API error and stable `app_expired` code for blocked API requests.

   Rationale: The frontend and tests need a predictable response status and shape. `403` accurately communicates that the app understood the request but refuses to perform it because the build is no longer allowed to run. This fits the existing `{ error, message }` API error convention and avoids treating expiry as an internal server error or authentication failure.

   Alternatives considered: use `401`, `410`, `permission_denied`, or `not_authenticated`. `401` and auth codes misrepresent the condition; `410` implies endpoint/resource retirement rather than app-level refusal.

4. Make expiry status deterministic when remote time lookup fails.

   Rationale: Current fail-open behavior can leave expired builds usable. The expiry check should use the remote UTC date when available and fall back to the local UTC date, so a transient time API outage does not automatically disable enforcement.

   Alternatives considered: always fail closed on time API errors. That prevents expired usage but can lock out valid builds unnecessarily when offline before the expiry date.

5. Keep the existing beta status response shape unless implementation reveals a stronger need.

   Rationale: `BetaStatusResponse` already has the fields needed by the frontend (`is_beta`, `expired`, `expires_on`, `days_remaining`). Avoiding schema churn keeps this change focused.

   Alternatives considered: rename beta endpoints/types to generic expiry endpoints. That is cleaner long term but increases scope and risks unrelated regressions.

6. Have the sorter check expiry between files and emit a terminal SSE error when expiry is reached during active sorting.

   Rationale: A route guard only blocks new requests; it does not stop an already-running background sort. Checking before each file prevents additional moves/copies after expiry while avoiding unsafe interruption of a single file operation already in progress. Emitting a terminal `error` progress event gives existing EventSource clients a structured signal that sorting stopped because the app expired.

   Alternatives considered: allow active sorts to finish, or forcibly kill the worker thread. Allowing completion violates the expiry requirement; forcibly interrupting file operations risks partial or corrupt filesystem state.

7. Handle EventSource failures by rechecking expiry status on the frontend.

   Rationale: If a new `/api/sort/progress` EventSource connection is refused by the backend guard, browser EventSource handlers cannot read the JSON error body. Rechecking `/api/app/beta` lets the frontend reliably route to the expiration screen even when the stream fails before receiving an SSE event.

   Alternatives considered: exempt all sort progress requests after expiry. That leaves a protected API stream available indefinitely and complicates the route guard; active streams already get terminal SSE events from the sorter.

## Risks / Trade-offs

- [Risk] Local system clock manipulation can bypass expiry when the remote time API is unavailable. -> Mitigation: prefer remote UTC time when available and keep fallback behavior covered by tests; stronger anti-tamper behavior belongs in a future licensing/activation change.
- [Risk] Middleware exemptions could accidentally leave a functional route accessible. -> Mitigation: use an allowlist of exempt paths and tests for representative protected routes across auth, albums, sorting, and settings.
- [Risk] Expiry could occur during a file move/copy operation. -> Mitigation: check expiry before each file and stop before the next filesystem operation; do not interrupt an operation already underway.
- [Risk] EventSource clients cannot inspect JSON error bodies from refused connections. -> Mitigation: emit a terminal SSE expiry event for active streams and recheck expiry status when the stream errors before receiving a terminal event.
- [Risk] The frontend may briefly show loading while the beta status request resolves. -> Mitigation: preserve the existing initialization order where beta status is checked before session routing.
- [Risk] Existing tests may assume beta check failures allow normal use. -> Mitigation: update tests to distinguish status endpoint/network failures from backend-enforced expired responses.
