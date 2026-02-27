# AGENTS.md — iCloud Photo Downloader

## Planning Documents

- **`PLANNING_MVP.md`** — Original MVP spec (album-level downloads, auth, architecture)
- **`PLANNING_FILE_SELECTION.md`** — File-level selection feature (extends MVP)

Both are sources of truth. When they conflict, `PLANNING_FILE_SELECTION.md` takes precedence for download-related behavior.

---

## API Contract

Backend implements in Pydantic schemas (`backend/models/schemas.py`); frontend matches in `frontend/src/types/api.ts`. Any change to the contract must update both sides.

### Standard Error Response

All error responses use this shape:

```json
{ "error": "<error_code>", "message": "<human-readable detail>" }
```

Error codes: `invalid_credentials`, `2fa_required`, `2fa_failed`, `session_expired`, `not_authenticated`, `not_found`, `download_in_progress`, `insufficient_disk_space`, `icloud_rate_limited`, `internal_error`

### Auth Endpoints

**`POST /api/auth/login`**
- Request: `{ "apple_id": string, "password": string }`
- Response (success): `{ "authenticated": true, "requires_2fa": false }`
- Response (2FA needed): `{ "authenticated": false, "requires_2fa": true }`

**`POST /api/auth/2fa`**
- Request: `{ "code": string }`
- Response: `{ "authenticated": true }`

**`GET /api/auth/session`**
- Response: `{ "authenticated": boolean, "apple_id": string | null, "requires_2fa": boolean }`

### Album Endpoints

**`GET /api/albums`**
- Response: `{ "albums": [{ "id": string, "name": string, "asset_count": number, "folder_name": string }] }`

**`GET /api/albums/:id/assets`**
- Query params: `offset` (int, default 0), `limit` (int, default 200)
- Response: `{ "assets": [{ "id": string, "filename": string, "size_bytes": number, "item_type": string, "created_at": string, "width": number, "height": number }], "total": number, "offset": number, "limit": number }`

### Download Endpoints

**`POST /api/download/start`**
- Request:
  ```json
  {
    "album_ids": ["..."],
    "asset_selections": { "album_id": ["asset_id_1", "asset_id_2"] },
    "download_path": "/path/to/downloads"
  }
  ```
  - `album_ids` (list, default `[]`): Download ALL assets from these albums
  - `asset_selections` (dict, optional): Download ONLY listed assets, keyed by album ID — each asset goes into that album's folder
  - Both fields can be used together in one request
  - See `PLANNING_FILE_SELECTION.md` for full specification
- Response: `{ "job_id": string, "total_assets": number, "estimated_bytes": number }`
- Error (disk): `{ "error": "insufficient_disk_space", "message": "...", "required_bytes": number, "available_bytes": number }`

**`GET /api/download/progress`** (SSE stream — see §SSE Progress Schema)

**`POST /api/download/pause`**
- Response: `{ "status": "paused" }`

**`POST /api/download/cancel`**
- Response: `{ "status": "cancelled" }`

### Settings Endpoints

**`GET /api/settings`**
- Response: `{ "download_path": string, "concurrent_downloads": number, "metadata_delay_ms": number, "max_retries": number }`

**`PUT /api/settings`**
- Request: same shape as GET response (partial updates allowed)
- Validation: `concurrent_downloads` 1–10, `metadata_delay_ms` ≥ 0, `max_retries` 1–10
- Response: full settings object after update

### SSE Progress Schema

The `GET /api/download/progress` endpoint streams `text/event-stream` events. Each event is a JSON payload:

```json
{
  "status": "downloading" | "paused" | "complete" | "cancelled" | "error",
  "total_assets": 1500,
  "completed_assets": 342,
  "failed_assets": 2,
  "skipped_assets": 0,
  "bytes_downloaded": 1073741824,
  "bytes_total": 5368709120,
  "current_file": "IMG_1234.HEIC",
  "current_album": "Vacation 2024",
  "speed_bytes_per_sec": 2500000,
  "eta_seconds": 1720,
  "errors": [
    { "asset_id": "abc", "filename": "IMG_0001.JPG", "error": "Network timeout", "attempts": 3 }
  ]
}
```

- Events emit every **0.5 seconds** while active
- When `status` is `"complete"`, `"cancelled"`, or `"error"`, it is the **terminal event** — the stream closes after sending it
- On `EventSource` reconnect, the server sends a **full snapshot** (not deltas)
- If auth expires mid-download, emit: `{ "status": "error", "error": "session_expired", "message": "Re-authentication required" }`

---

## Integration Checklist

Verify all of the following after changes that touch the API boundary:

1. **Build & serve:** `cd frontend && npm run build` succeeds; `cd backend && python app.py` serves both API and frontend at `http://localhost:8000`
2. **SPA routing:** refreshing on any frontend route (e.g., `/albums`) serves `index.html`, not a 404
3. **Dev proxy:** `npm run dev` on port 5173 proxies `/api/*` to backend on port 8000
4. **Type alignment:** every field in `frontend/src/types/api.ts` matches its counterpart in `backend/models/schemas.py`
5. **Auth flow:** `/api/auth/login` → 2FA prompt → `/api/auth/2fa` → `/api/auth/session` returns `authenticated: true`
6. **Album listing:** `/api/albums` returns correct shape; `/api/albums/:id/assets` paginates correctly
7. **Download (album):** `POST /api/download/start` with `album_ids` downloads all assets; SSE events match schema; pause/cancel work
8. **Download (file selection):** `POST /api/download/start` with `asset_selections` downloads only selected files into correct album folders
9. **Settings round-trip:** `GET /api/settings` → `PUT /api/settings` → `GET /api/settings` reflects changes
10. **Error handling:** invalid login returns `{ error: "invalid_credentials", message: "..." }` not a 500

---

## Code Review Tracker

Active code review issues are tracked in **`docs/CODE_REVIEW.md`**. Agents must:
- Check this file before working on related code
- Mark issues as fixed (`[x]`) when addressed
- Add new issues discovered during implementation

---

## Shared Conventions

- **No placeholders or TODO stubs** — every file should contain working code or complete content
- **API contract (defined above) is the integration boundary** — backend implements Pydantic schemas, frontend matches with TypeScript types
- **Python:** 3.10+, type hints, f-strings, `asyncio`
- **TypeScript:** strict mode, no `any` types
- **File paths:** use the project structure from `PLANNING_MVP.md` §9
