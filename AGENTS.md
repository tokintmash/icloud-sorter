# AGENTS.md — iCloud Photo Downloader

## Architecture

One **orchestrator agent** coordinates three **subagents** that work in parallel on independent areas of the codebase.

---

## Orchestrator (Main Agent)

**Role:** Plans work, defines the API contract, delegates to subagents, reviews integration points, resolves cross-boundary issues.

**Responsibilities:**
- Break implementation phases from `PLANNING_MVP.md` into concrete tasks for subagents
- **Define the API contract (see §API Contract below) before subagents start** — this is a blocking prerequisite
- Verify frontend types match backend Pydantic schemas
- Run the integration checklist (see §Integration Checklist) after subagents complete
- Handle any conflicts or dependencies between subagents

**Code authority:** The orchestrator avoids feature work, but **may make minimal cross-cutting integration edits** (schemas, wiring, config, type alignment) to keep the build coherent. For example: adjusting a Pydantic response field and updating the matching TypeScript type in the same pass.

---

## API Contract

The orchestrator **must** define this contract before subagents begin. Backend implements it in Pydantic schemas; frontend matches it in `types/api.ts`.

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
- Request: `{ "album_ids": string[], "download_path": string }`
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

## Subagent 1: Backend

**Scope:** Everything under `backend/`

**Owns:**
- `backend/app.py` — FastAPI entry point, CORS, static file serving, SPA fallback
- `backend/routers/` — `auth.py`, `albums.py`, `download.py`, `settings.py`
- `backend/services/` — `icloud_service.py`, `download_service.py`, `state_service.py`
- `backend/models/` — `schemas.py` (Pydantic models), `db.py` (SQLite schema + queries)
- `backend/config.py` — configuration defaults
- `backend/requirements.txt`

**Key constraints:**
- Use `pyicloud` (timlaing fork) directly — no subprocess bridge
- FastAPI with async endpoints; downloads in `ThreadPoolExecutor` (pyicloud is sync)
- SSE for progress streaming (`text/event-stream`), not WebSockets
- SQLite via stdlib `sqlite3` — no ORM
- Follow the API contract defined above exactly
- Follow the SQLite schema in `PLANNING_MVP.md` §5 exactly
- State DB location: `~/.icloud-downloader/state.db`
- `app.py` must work with both `python app.py` (direct execution with `uvicorn.run()`) and `uvicorn backend.app:app`
- Serve `frontend/dist/` as static files in production; include SPA history fallback (serve `index.html` for non-API, non-static routes)
- CORS: allow `http://localhost:5173` in dev (Vite dev server default)

**Media type handling (from §6):**
- JPEG/PNG: download original
- HEIC: download original (no conversion)
- Live Photos: download **both** image + video (two files per asset)
- Videos: download as-is
- Edited photos: download **original only** (MVP)
- RAW+JPEG: download **both** files
- Bursts: download all frames

**Filename & folder rules (from §7):**
- Collision resolution: append EXIF date on first collision (`IMG_0001_2024-03-15.HEIC`), then sequence number on further collision (`IMG_0001_2024-03-15 (2).HEIC`)
- Cross-album duplicates: download into each album folder independently; optimize by **copying the local file** if same `asset_id + version` already has `status = 'complete'`
- Album → folder name sanitization: replace `/ \ : * ? " < > |` with `_`, trim leading/trailing whitespace and dots, truncate to 200 chars, use `"Unnamed Album"` if empty, append `" (2)"` etc. on folder name collision

**Download pipeline (from §8):**
- Atomic writes: temp file `<album_folder>/.IMG_1234.HEIC.tmp` → rename on completion after size verification
- On startup: delete any leftover `.tmp` files (interrupted downloads)
- No partial resume in MVP — delete `.tmp` and re-download; skip completed files via `downloads` table
- Pause: set flag, workers finish current file then wait
- Cancel: set flag, workers finish current file then stop; delete `.tmp` files; mark remaining `pending` as `skipped`
- Disk space: pre-flight check via `shutil.disk_usage()`, re-check every 100 files or 1 GB, pause if <500 MB remaining

**Rate limiting (from §3):**
- Concurrent downloads: default 3, configurable 1–10
- Metadata delay: default 200ms, configurable
- 503 retry: exponential backoff starting at **30 seconds**, honor `retryAfter` header
- Max retries per asset: **3**

**Error handling (from §4):**
- HTTP 503: retry with backoff, honor `retryAfter`
- HTTP 401/403: re-authenticate; if 2FA needed, signal frontend via SSE `session_expired` status
- Network timeout: retry up to 3 times with backoff
- Disk write error: fail the asset, log error, continue with next
- Disk space exhausted: pause all downloads, alert user via SSE

**Testing:** Verify endpoints return correct shapes by checking against Pydantic schemas. Confirm the server starts with `python app.py` and `/docs` renders. Confirm `frontend/dist/` is served correctly when present.

---

## Subagent 2: Frontend

**Scope:** Everything under `frontend/`

**Owns:**
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`
- `frontend/index.html`
- `frontend/src/App.tsx`
- `frontend/src/components/` — `AuthScreen.tsx`, `AlbumBrowser.tsx`, `DownloadProgress.tsx`, `Settings.tsx`
- `frontend/src/hooks/useApi.ts`
- `frontend/src/types/api.ts`
- `frontend/src/styles/`

**Key constraints:**
- React + TypeScript, scaffolded with Vite
- TypeScript types in `types/api.ts` must match the API contract defined above exactly
- API calls go to `/api/*` (proxy to `http://localhost:8000` in dev via Vite config)
- SSE via `EventSource` for download progress — match the SSE Progress Schema above; handle reconnection (server sends full snapshot)
- Handle `session_expired` SSE status by redirecting user to re-authenticate
- Production build outputs to `frontend/dist/` which FastAPI serves as static files
- No external UI framework required — keep it simple (plain CSS or minimal library)
- Settings UI must expose: `download_path`, `concurrent_downloads` (1–10), `metadata_delay_ms`, `max_retries`
- Download Progress screen: show per-album progress, overall progress bar, speed, ETA, per-file error list with retry count
- Handle error responses using the standard error shape: `{ error, message }`
- Auth flow state machine: `unauthenticated` → `awaiting_2fa` → `authenticated` (and `authenticated` → `session_expired` → `unauthenticated`)

**Testing:** `npm run build` succeeds with zero TypeScript errors. Dev server starts with `npm run dev`.

---

## Subagent 3: Docs & Project Setup

**Scope:** Root-level files and `docs/`

**Owns:**
- `README.md` — project overview, setup instructions (clone → run), screenshots placeholder
- `docs/PREREQUISITES.md` — iCloud settings users must configure (ADP off, web access on, TOS accepted)
- `docs/DEVELOPMENT.md` — developer setup (Python venv, Node, running backend + frontend)
- `DISCLAIMER.md` — Apple TOS disclaimer, unofficial project notice
- `LICENSE` — MIT
- `.gitignore` — Python (`venv/`, `__pycache__/`, `*.pyc`, `.env`), Node (`node_modules/`, `frontend/dist/`), app data (`*.db`, `.tmp`)

**Key constraints:**
- Setup instructions must match the actual project structure created by Subagents 1 and 2
- Prerequisites must prominently warn about "Access iCloud Data on the Web" and Advanced Data Protection
- README should include the user setup commands from `PLANNING_MVP.md` §10
- DEVELOPMENT.md must document: running backend (`python app.py` on port 8000), running frontend dev server (`npm run dev` on port 5173), Vite proxy to backend
- Do not duplicate the full planning docs — reference `PLANNING_MVP.md` for architecture details

**Dependencies:** Waits for Subagents 1 and 2 to finalize file structure before writing setup instructions. Can start with `DISCLAIMER.md`, `LICENSE`, `.gitignore`, and `PREREQUISITES.md` immediately.

---

## Integration Checklist

The orchestrator **must** verify all of the following after subagents complete:

1. **Build & serve:** `cd frontend && npm run build` succeeds; `cd backend && python app.py` serves both API and frontend at `http://localhost:8000`
2. **SPA routing:** refreshing on any frontend route (e.g., `/albums`) serves `index.html`, not a 404
3. **Dev proxy:** `npm run dev` on port 5173 proxies `/api/*` to backend on port 8000
4. **Type alignment:** every field in `frontend/src/types/api.ts` matches its counterpart in `backend/models/schemas.py`
5. **Auth flow:** `/api/auth/login` → 2FA prompt → `/api/auth/2fa` → `/api/auth/session` returns `authenticated: true`
6. **Album listing:** `/api/albums` returns correct shape; `/api/albums/:id/assets` paginates correctly
7. **Download + SSE:** `/api/download/start` triggers downloads; `EventSource` on `/api/download/progress` receives events matching the SSE schema; pause/cancel work
8. **Settings round-trip:** `GET /api/settings` → `PUT /api/settings` → `GET /api/settings` reflects changes
9. **Error handling:** invalid login returns `{ error: "invalid_credentials", message: "..." }` not a 500

---

## Shared Conventions

- **No placeholders or TODO stubs** — every file should contain working code or complete content
- **Follow `PLANNING_MVP.md`** as the source of truth for all technical decisions
- **API contract (defined above) is the integration boundary** — backend implements Pydantic schemas, frontend matches with TypeScript types
- **Python:** 3.10+, type hints, f-strings, `asyncio`
- **TypeScript:** strict mode, no `any` types
- **File paths:** use the project structure from `PLANNING_MVP.md` §9 exactly
