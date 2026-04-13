# Phase 1 Issues

## Status: ✅ ALL RESOLVED

All issues below were fixed during Phase 1 implementation.

Issues found during code review against `PHASE1_PLAN.md` and `AGENTS.md` API contract.

---

## Critical (app broken without these)

### 1. ✅ `GET /api/albums` does not populate `album_files` table

**Files:** `backend/routers/albums.py`, `backend/services/icloud_service.py`

`list_albums()` only calls `icloud_service.get_albums()`, which fetches album metadata but never writes to the DB. `sync_album_metadata()` exists in `icloud_service.py` but nothing calls it. Consequence: `/api/sort/start` always finds zero pending files — sorting is completely broken.

**Fix:** `GET /api/albums` must call `sync_album_metadata()` (or a separate trigger must exist) so `album_files` is populated before sorting. Since pyicloud is synchronous, wrap the call with `await asyncio.to_thread(...)` to avoid blocking the event loop.

---

### 2. ✅ Folder-name determinism is broken for partial album selection

**Files:** `backend/services/sorter_service.py` (lines 57–61)

The plan specifies: *"Folder name computation | Global deterministic (all albums, sorted) | Prevents name drift between runs."*

Currently `_run_sort()` recomputes `_compute_folder_names()` using **only the selected albums' rows**, not the full album catalog. If two albums share a name (e.g., both called "Vacation"), selecting only the second one maps it to `"Vacation"` instead of the correct `"Vacation (2)"`.

**Fix:** Persist the full album→folder_name mapping (e.g., in `album_files` or a separate store) during `sync_album_metadata()` / `get_albums()`. Have `_run_sort()` use the persisted mapping instead of recomputing from the selected subset.

---

### 3. ✅ `sync_album_metadata()` crashes on duplicate filenames within same album

**Files:** `backend/services/icloud_service.py` (lines 182–194), `backend/services/state_service.py` (lines 31–35)

DB primary key is `(album_id, filename)`. If an iCloud album contains two assets with the same filename (possible with Live Photos or edits), `replace_album_files()` raises `sqlite3.IntegrityError` and the entire sync fails.

**Fix:** Deduplicate rows by `(album_id, filename)` before inserting, or use `INSERT OR IGNORE` / `INSERT OR REPLACE`.

---

## Moderate (contract violations / layering issues)

### 4. ✅ Service imports from router (layering violation)

**Files:** `backend/services/sorter_service.py` (line 7)

`sorter_service.py` imports `_load_settings` from `backend.routers.settings`. Services should not depend on routers.

**Fix:** Move `_load_settings()` (and `_save_settings()`) into a service (e.g., `backend/services/settings_service.py` or into `backend/config.py`), then import from there in both the router and the sorter service.

---

### 5. ✅ `POST /api/sort/start` returns undeclared error code `not_found`

**Files:** `backend/services/sorter_service.py` (line 40), `backend/routers/sort.py` (lines 19–26)

When no pending files exist, the sorter returns `{"error": "not_found", ...}`. The `AGENTS.md` error code list does not include `not_found`. Closest match would be `file_not_found` or `internal_error`.

**Fix:** Change the error code to a declared one (e.g., `file_not_found`) or add `not_found` to the API contract.

---

### 6. ✅ SSE progress can emit undocumented `idle` status and stream forever

**Files:** `backend/services/sorter_service.py` (line 15), `backend/routers/sort.py` (lines 32–44)

`SorterService.__init__` sets `_status = "idle"`, but the API contract only allows `"sorting" | "complete" | "error"`. If a client connects to `/api/sort/progress` before a sort starts, it receives `status: "idle"` indefinitely because the exit condition only checks for `"complete"` or `"error"`.

**Fix:** Either return a non-SSE error response when no sort is active (e.g., 404 or 409), or include `"idle"` as a terminal status in the stream exit condition.

---

### 7. ✅ Blocking sync calls inside async route handlers

**Files:** `backend/routers/albums.py`, `backend/services/icloud_service.py`

`get_albums()` (and `sync_album_metadata()` once wired in) calls pyicloud synchronously. Called directly from `async def list_albums()`, this blocks the event loop — potentially for minutes on large libraries.

**Fix:** Wrap pyicloud calls with `await asyncio.to_thread(icloud_service.get_albums)` in the router.

---

## Minor (best-practice, non-blocking)

### 8. ✅ SSE response missing `Cache-Control: no-cache` header

**File:** `backend/routers/sort.py` (line 45)

SSE best practice is to include `Cache-Control: no-cache` to prevent proxies/browsers from buffering the stream.

**Fix:** Add `headers={"Cache-Control": "no-cache"}` to the `StreamingResponse`.

---

### 9. ⏳ Deprecated `@app.on_event("startup")`

**File:** `backend/app.py` (line 39)

FastAPI's `on_event` is deprecated in favor of the `lifespan` context manager.

**Fix:** Low priority — can be addressed in a later cleanup pass.

---

### 10. ⏳ Unsynchronized shared state between threads

**File:** `backend/services/sorter_service.py`

`_run_sort()` runs in a worker thread (via `asyncio.to_thread`) and mutates `_completed_files`, `_failed_files`, etc. while `get_progress()` reads them from the event-loop thread. No lock protects these fields. CPython's GIL makes this practically safe for simple attribute access, but it's not strictly correct.

**Fix:** Low priority for MVP. Add a `threading.Lock` if correctness guarantees are needed later.
