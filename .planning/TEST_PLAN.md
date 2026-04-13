# Test Plan: iCloud Photo Sorter

## Backend (Python — `pytest`)

**Dependencies to add:** `pytest`, `pytest-asyncio`, `httpx` (for FastAPI `TestClient`)

### 1. `backend/tests/test_state_service.py` — State/DB layer
- **`replace_album_files`** — inserts rows, replaces by album_id, handles empty list
- **`replace_album_files`** — `album_ids=None` performs full wipe before insert
- **`get_album_summaries`** — correct aggregation (total, sorted, failed counts)
- **`reset_album_files`** — resets status to pending, clears error
- **`get_pending_album_files`** — returns only pending rows for given album_ids
- **`get_pending_album_files`** — empty `album_ids` list returns empty result
- **`mark_album_file_sorted` / `mark_album_file_failed`** — updates status correctly
- **`save_session` / `get_session`** — round-trip, handles missing/corrupt file

### 2. `backend/tests/test_icloud_service.py` — iCloud service (mocked `pyicloud`)
- **`_sanitize_folder_name`** — strips invalid chars, trims dots/whitespace, truncates at 200, empty → `"Unnamed Album"`
- **`_compute_folder_names`** — deduplicates identical folder names with `(2)`, `(3)` etc.
- **`_compute_folder_names`** — different raw names that sanitize to the same folder name (e.g. `"a/b"` and `"a:b"` → `"a_b"`, `"a_b (2)"`).
- **`_get_asset_filename`** — plain filename, base64-encoded filename, fallback to `filenameEnc`, returns `None` on failure
- **`login`** — success, requires_2fa, invalid credentials, API error (all mocked)
- **`validate_2fa`** — success, invalid code, no active session
- **`get_session_status`** — unauthenticated, awaiting 2fa, authenticated
- **`get_albums`** — returns correct shape, handles API error, unauthenticated
- **`sync_album_metadata`** — populates DB, filters by album_ids, handles bad assets

### 3. `backend/tests/test_sorter_service.py` — Sorter engine (file system mocked with `tmp_path`)
- **Happy path** — moves files into album-named folders, marks sorted
- **File not found** — marks failed, continues
- **File already in target dir** — marks sorted without moving
- **Filename collision** — appends `(2)`, `(3)` suffix
- **Cross-album duplicate** — first album gets the file, second is skipped/failed
- **Case-insensitive matching** — `IMG_001.HEIC` matches `img_001.heic`
- **Permission error** — marks failed, continues
- **Sort already in progress** — returns error
- **File index updated after move** — file moved for album A is still findable by album B via updated index
- **Empty `album_ids` list** — returns error (no files to sort)
- **Invalid `icloud_folder` path** — returns `file_not_found` error
- **Unauthenticated** — returns `not_authenticated` error

### 4. `backend/tests/test_config.py` — Config/settings
- **`_detect_icloud_folder`** — returns first existing path, empty if none
- **`load_settings` / `save_settings`** — round-trip, handles missing file, corrupt JSON

### 5. `backend/tests/test_routers.py` — API integration (FastAPI `TestClient`, services mocked)
- **`POST /api/auth/login`** — 200 on success, 401 on bad credentials, 200 with `requires_2fa`
- **`POST /api/auth/2fa`** — 200 on success, 401 on invalid code
- **`GET /api/auth/session`** — returns correct session state
- **`GET /api/albums`** — 200 with album list, 401 if unauthenticated
- **`POST /api/sort/start`** — 200, 409 if already running, 401 if not authenticated
- **`GET /api/sort/progress`** — SSE stream emits correct JSON events
- **`GET /api/settings`** / **`PUT /api/settings`** — round-trip, partial update
- **`GET /api/sort/progress`** — 409 when no sort is active
- **`POST /api/sort/start`** — 400 with empty `album_ids`
- **`POST /api/sort/start`** — 400 when `icloud_folder` is unconfigured

### 6. `backend/tests/test_db.py` — Database init
- **`init_db` idempotency** — calling twice does not error, schema is correct
- **Schema verification** — `album_files` table has expected columns and indexes

### 7. `backend/tests/test_app.py` — App / SPA fallback
- **API 404** — `GET /api/nonexistent` returns `{"error": "not_found"}` JSON
- **SPA fallback** — non-API path returns `index.html` when frontend is built
- **Missing frontend dist** — returns 404 JSON when `frontend/dist/` doesn't exist
- **Static asset serving** — `GET /assets/...` serves files from `frontend/dist/assets/`

---

## Frontend (TypeScript — `vitest` + `@testing-library/react`)

**Dependencies to add:** `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`

### 8. `frontend/src/hooks/__tests__/useApi.test.ts` — API client
- **`apiFetch`** — sets `Content-Type` for POST/PUT, parses JSON response
- **`ApiError`** — thrown on non-OK response with `{ error, message }` body
- **Error fallback** — non-JSON error body → `internal_error`
- Each endpoint function — calls correct URL/method/body

### 9. `frontend/src/components/__tests__/AuthScreen.test.tsx`
- Renders login form by default
- Renders 2FA form when `initialMode="2fa"`
- Submit login → calls `login()`, transitions to 2FA on `requires_2fa`
- Submit login → calls `onAuthenticated` on success
- Shows error on `ApiError`
- Disables button while loading / when fields empty

### 10. `frontend/src/components/__tests__/AlbumPicker.test.tsx`
- Renders loading spinner, then album list
- Select/deselect individual albums via checkbox
- Select All / Deselect All
- "Sort Selected" button disabled when none selected, enabled otherwise
- Calls `onStartSort` with selected album IDs
- Shows error + Retry on API failure
- Calls `onSessionExpired` on `not_authenticated` error

### 11. `frontend/src/components/__tests__/SortProgress.test.tsx`
- Shows "Starting sort…" spinner initially
- Shows progress bar and stats after SSE events
- Shows current file/album
- Shows error list, "Show all" toggle for >5 errors
- Shows completion summary on `status: "complete"`
- Calls `onComplete` when "Done" clicked
- Handles `startSort` failure → error message + "Back to Albums"

### 12. `frontend/src/components/__tests__/Settings.test.tsx`
- Loads and displays current `icloud_folder`
- Saves updated value, shows success message
- Shows error on save failure

### 13. `frontend/src/App.test.tsx`
- Loading state → spinner
- Unauthenticated → shows `AuthScreen`
- Authenticated → shows nav + `AlbumPicker`
- Tab navigation (Albums / Sorting / Settings)
- `onStartSort` → switches to Sorting tab with album IDs
- `onSessionExpired` → returns to login

---

## Test Infrastructure

| Concern | Backend | Frontend |
|---|---|---|
| **Runner** | `pytest` | `vitest` |
| **Mocking** | `unittest.mock` / `monkeypatch` | `vi.mock` / `vi.fn` |
| **DB** | In-memory SQLite via `tmp_path` override of `STATE_DB_PATH` | N/A |
| **File system** | `tmp_path` for sorter tests | N/A |
| **Network** | Mock `pyicloud`; `TestClient` for routers | `vi.mock('../hooks/useApi')` |
| **SSE** | `TestClient` stream response | Mock `EventSource` globally |
