# Backend — Agent Instructions

## Scope

Everything under `backend/`. Key files:

- `app.py` — FastAPI entry point, CORS, static file serving, SPA fallback
- `routers/` — `auth.py`, `albums.py`, `download.py`, `settings.py`
- `services/` — `icloud_service.py`, `download_service.py`, `state_service.py`
- `models/` — `schemas.py` (Pydantic models), `db.py` (SQLite schema + queries)
- `config.py` — configuration defaults
- `requirements.txt`

---

## Constraints

- Use `pyicloud` (timlaing fork) directly — no subprocess bridge
- FastAPI with async endpoints; downloads in `ThreadPoolExecutor` (pyicloud is sync)
- SSE for progress streaming (`text/event-stream`), not WebSockets
- SQLite via stdlib `sqlite3` — no ORM
- Follow the API contract in root `AGENTS.md` exactly
- State DB location: `~/.icloud-downloader/state.db`
- `app.py` must work with both `python app.py` (direct execution with `uvicorn.run()`) and `uvicorn backend.app:app`
- Serve `frontend/dist/` as static files in production; include SPA history fallback (serve `index.html` for non-API, non-static routes)
- CORS: allow `http://localhost:5173` in dev (Vite dev server default)

---

## Media Type Handling (from PLANNING_MVP.md §6)

- JPEG/PNG: download original
- HEIC: download original (no conversion)
- Live Photos: download **both** image + video (two files per asset)
- Videos: download as-is
- Edited photos: download **original only**
- RAW+JPEG: download **both** files
- Bursts: download all frames

---

## Filename & Folder Rules (from PLANNING_MVP.md §7)

- Collision resolution: append EXIF date on first collision (`IMG_0001_2024-03-15.HEIC`), then sequence number on further collision (`IMG_0001_2024-03-15 (2).HEIC`)
- Cross-album duplicates: download into each album folder independently; optimize by **copying the local file** if same `asset_id + version` already has `status = 'complete'`
- Album → folder name sanitization: replace `/ \ : * ? " < > |` with `_`, trim leading/trailing whitespace and dots, truncate to 200 chars, use `"Unnamed Album"` if empty, append `" (2)"` etc. on folder name collision

---

## Download Pipeline (from PLANNING_MVP.md §8)

- Atomic writes: temp file `<album_folder>/.IMG_1234.HEIC.tmp` → rename on completion after size verification
- On startup: delete any leftover `.tmp` files (interrupted downloads)
- No partial resume — delete `.tmp` and re-download; skip completed files via `downloads` table
- Pause: set flag, workers finish current file then wait
- Cancel: set flag, workers finish current file then stop; delete `.tmp` files; mark remaining `pending` as `skipped`
- Disk space: pre-flight check via `shutil.disk_usage()`, re-check every 100 files or 1 GB, pause if <500 MB remaining

---

## Rate Limiting (from PLANNING_MVP.md §3)

- Concurrent downloads: default 3, configurable 1–10
- Metadata delay: default 200ms, configurable
- 503 retry: exponential backoff starting at **30 seconds**, honor `retryAfter` header
- Max retries per asset: **3**

---

## Error Handling (from PLANNING_MVP.md §4)

- HTTP 503: retry with backoff, honor `retryAfter`
- HTTP 401/403: re-authenticate; if 2FA needed, signal frontend via SSE `session_expired` status
- Network timeout: retry up to 3 times with backoff
- Disk write error: fail the asset, log error, continue with next
- Disk space exhausted: pause all downloads, alert user via SSE

---

## Testing

- Verify endpoints return correct shapes by checking against Pydantic schemas
- Confirm the server starts with `python app.py` and `/docs` renders
- Confirm `frontend/dist/` is served correctly when present

---

## Code Review Notes

### pyicloud `AlbumContainer` iteration

`photos.albums` returns an `AlbumContainer` object, **not a Python dict**. It has no `.values()` method. Iterating it directly (`for album in photos.albums:`) yields album objects — `AlbumContainer.__iter__` calls `iter(self._albums.values())` internally.

- ✅ Correct: `for album in photos.albums:`
- ❌ Wrong: `for album in photos.albums.values():` — raises `AttributeError: 'AlbumContainer' object has no attribute 'values'`

This was verified against the installed pyicloud source (`pyicloud/services/photos.py`).

### pyicloud `PhotoAsset.download()` returns raw bytes

`asset.download(version)` returns `bytes` (via `response.raw.read()`), **not** a `Response` object. Do NOT call `.content` on the result.

- ✅ Correct: `data = asset.download("original")` → `data` is `bytes | None`
- ❌ Wrong: `response = asset.download("original"); data = response.content` → `AttributeError`

If the requested version is not in `asset.versions`, `download()` returns `None`.

### Download records get stuck on interrupted runs

The `downloads` table uses `INSERT OR IGNORE` (keyed on `asset_id, album_id, version`). Records from a previous interrupted/cancelled run can get stuck in `'downloading'`, `'skipped'`, or `'failed'` (with exhausted retries) status. On re-run, `INSERT OR IGNORE` silently skips them and `get_pending_downloads` won't return them, causing an empty download that reports success with 0 files.

**Mitigation:** Always call `reset_stale_downloads(album_ids)` before `create_download_records()` to reset all non-`'complete'` records back to `'pending'`.
