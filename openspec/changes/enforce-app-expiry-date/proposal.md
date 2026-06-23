## Why

The app already exposes a beta/expiry date, but expiration is only advisory and the app can remain usable after that date has passed. Expired builds must stop functioning reliably so users cannot continue sorting or accessing app features past the allowed window.

## What Changes

- Enforce the build expiry date in the backend so protected API operations are blocked after expiration.
- Stop active sorting when expiry is reached so work that started before expiry does not continue moving or copying files afterward.
- Preserve a frontend expired-build screen, but make it reflect backend-enforced state rather than being the only control.
- Return a stable API error and HTTP status when an expired build blocks an operation.
- Keep unstamped development builds usable so local development is not blocked.

## Capabilities

### New Capabilities
- `app-expiry`: Defines how stamped builds determine expiry and how expired builds are prevented from functioning.

### Modified Capabilities
- `frontend-flow`: Require expired builds to route to an expiration screen before consent, authentication, album selection, sorting, or settings.
- `api-errors`: Add the stable error response expected when an expired build blocks a backend operation.
- `sort-progress`: Define how active sort progress reports expiry when expiration is reached during an SSE-observed sort.

## Impact

- Backend: `backend/beta.py`, `backend/app.py`, routers or middleware that guard protected API routes, `backend/services/sorter_service.py`, SSE progress handling, and related tests.
- Frontend: `frontend/src/App.tsx`, API types/hooks, and tests for expired-build routing and API error handling.
- API contract: adds a stable expired-build error code and status for blocked protected API requests, plus terminal sort progress behavior for expiry during active sorting.
- Packaging/build stamping: existing beta stamp behavior remains the source of the expiry date for stamped builds.
