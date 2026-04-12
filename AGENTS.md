# AGENTS.md — iCloud Photo Sorter

## Overview

This app reads iCloud album metadata via `pyicloud`, matches it to files already synced locally by iCloud for Windows, and moves them into album-named folders. **No downloading** — files are reorganized in place.

**Source of truth:** `PLANNING_SORTER_v2.md`

---

## Architecture

FastAPI backend + React frontend. One SQLite table (`album_files`) tracks everything.

```
User authenticates (pyicloud) → App fetches album/file metadata →
User picks albums → Sorter moves files into album folders → Done
```

---

## API Contract

Backend implements in Pydantic schemas (`backend/models/schemas.py`); frontend matches in `frontend/src/types/api.ts`.

### Standard Error Response

```json
{ "error": "<error_code>", "message": "<human-readable detail>" }
```

Error codes: `invalid_credentials`, `2fa_required`, `2fa_failed`, `session_expired`, `not_authenticated`, `sort_in_progress`, `file_not_found`, `permission_denied`, `internal_error`

### Auth Endpoints

**`POST /api/auth/login`**
- Request: `{ "apple_id": string, "password": string }`
- Response: `{ "authenticated": true, "requires_2fa": false }` or `{ "authenticated": false, "requires_2fa": true }`

**`POST /api/auth/2fa`**
- Request: `{ "code": string }`
- Response: `{ "authenticated": true }`

**`GET /api/auth/session`**
- Response: `{ "authenticated": boolean, "apple_id": string | null, "requires_2fa": boolean }`

### Album Endpoints

**`GET /api/albums`**
- Response: `{ "albums": [{ "id": string, "name": string, "asset_count": number, "folder_name": string }] }`

### Sort Endpoints

**`POST /api/sort/start`**
- Request: `{ "album_ids": string[] }`
- Response: `{ "total_files": number }`

**`GET /api/sort/progress`** (SSE stream)
```json
{
  "status": "sorting" | "complete" | "error",
  "total_files": 1500,
  "completed_files": 342,
  "failed_files": 2,
  "current_file": "IMG_1234.HEIC",
  "current_album": "Vacation 2024",
  "errors": [
    { "filename": "IMG_0001.JPG", "error": "File not found", "album": "Vacation" }
  ]
}
```

### Settings Endpoints

**`GET /api/settings`**
- Response: `{ "icloud_folder": string }`

**`PUT /api/settings`**
- Partial updates allowed
- Response: full settings after update

---

## SQLite Schema

One table. Location: `~/.icloud-sorter/state.db`

```sql
CREATE TABLE album_files (
    album_id    TEXT NOT NULL,
    album_name  TEXT NOT NULL,
    filename    TEXT NOT NULL,
    status      TEXT DEFAULT 'pending',  -- 'pending', 'sorted', 'failed'
    error       TEXT,
    PRIMARY KEY (album_id, filename)
);
```

---

## Backend

**Scope:** Everything under `backend/`

**Files:**
- `backend/app.py` — FastAPI entry, CORS, SPA fallback
- `backend/routers/auth.py` — login, 2FA, session check
- `backend/routers/albums.py` — album list from iCloud
- `backend/routers/sort.py` — start sort, SSE progress
- `backend/routers/settings.py` — iCloud folder path
- `backend/services/icloud_service.py` — pyicloud auth + album/asset metadata
- `backend/services/sorter_service.py` — file move engine
- `backend/services/state_service.py` — SQLite queries (one table)
- `backend/models/schemas.py` — Pydantic models
- `backend/models/db.py` — SQLite schema + init
- `backend/config.py` — paths & defaults

**Key constraints:**
- `pyicloud` (timlaing fork) called directly — no subprocess
- FastAPI with async endpoints; file ops in `ThreadPoolExecutor` (pyicloud is sync)
- SSE for progress streaming, not WebSockets
- SQLite via stdlib `sqlite3` — no ORM
- `app.py` works with both `python app.py` and `uvicorn backend.app:app`
- Serve `frontend/dist/` as static files; SPA fallback for non-API routes
- CORS: allow `http://localhost:5173` in dev

**Sorter engine rules:**
- Files are **moved** (not copied) within the iCloud Photos folder — instant on same drive
- Album → folder name sanitization: replace `/ \ : * ? " < > |` with `_`, trim whitespace/dots, truncate to 200 chars, `"Unnamed Album"` if empty
- Filename collision in target folder: append sequence number `IMG_0001 (2).HEIC`
- Cross-album duplicates (MVP): move to first album, skip in subsequent
- Case-insensitive filename matching (Windows NTFS)
- Files not found locally: mark as `failed` with error, continue with next

---

## Frontend

**Scope:** Everything under `frontend/`

**Files:**
- `frontend/src/App.tsx` — root, auth state machine, screen routing
- `frontend/src/components/AuthScreen.tsx` — Apple ID login + 2FA
- `frontend/src/components/AlbumPicker.tsx` — album list with checkboxes, counts, sort button
- `frontend/src/components/SortProgress.tsx` — progress bar, current file, errors, completion
- `frontend/src/components/Settings.tsx` — iCloud folder path config
- `frontend/src/hooks/useApi.ts` — `apiFetch<T>()` + typed endpoint functions
- `frontend/src/types/api.ts` — TypeScript types matching backend schemas
- `frontend/src/styles/index.css` — CSS design system

**Key constraints:**
- React + TypeScript + Vite
- Types in `types/api.ts` must match API contract exactly
- API calls to `/api/*`, proxied to `http://localhost:8000` in dev via Vite config
- SSE via `EventSource` for sort progress
- No external UI framework — plain CSS
- Auth state machine: `unauthenticated` → `awaiting_2fa` → `authenticated`
- Build outputs to `frontend/dist/`

**Screens (linear flow + settings):**
1. **Auth** — login + 2FA
2. **Album Picker** — checkboxes, file counts, previously-sorted indicators, "Sort Selected" button
3. **Sort Progress** — progress bar, current file/album, error list, completion summary
4. **Settings** (via icon/tab) — iCloud folder path

---

## Integration Checklist

1. `cd frontend && npm run build` succeeds with zero TS errors
2. `python backend/app.py` serves API + frontend at `http://localhost:8000`
3. `npm run dev` proxies `/api/*` to backend on port 8000
4. Every field in `types/api.ts` matches its counterpart in `schemas.py`
5. Auth flow: login → 2FA → session returns `authenticated: true`
6. Album listing returns correct shape
7. Sort: `/api/sort/start` moves files; SSE progress events match schema
8. Settings round-trip: GET → PUT → GET reflects changes
9. Errors return `{ error, message }` not 500s

---

## Code Review Notes

### pyicloud `AlbumContainer` iteration

`photos.albums` returns an `AlbumContainer`, **not a dict**. No `.values()` method.

- ✅ `for album in photos.albums:`
- ❌ `for album in photos.albums.values():` — `AttributeError`

### pyicloud `PhotoAsset.download()` returns raw bytes

Not needed for the sorter (we don't download files), but noted for reference: `asset.download(version)` returns `bytes`, not a `Response` object.

---

## Conventions

- **No placeholders or TODO stubs** — every file must contain working code
- **`PLANNING_SORTER_v2.md`** is the source of truth
- **Python:** 3.10+, type hints, f-strings, `asyncio`
- **TypeScript:** strict mode, no `any` types
- **No licensing in MVP** — deferred to post-MVP
