# Phase 1: Core Sorter Backend — Implementation Plan

**Source of truth:** `.planning/PLANNING_SORTER_v2.md`  
**Scope:** Replace the download-based backend with a file-sorting backend. No frontend changes.

---

## Current State

The backend is a **photo downloader**: multi-table SQLite schema (sessions, albums, assets, album_assets, downloads), a `DownloadService` with pause/resume/cancel/retry, byte-level progress, and download-specific settings (concurrent_downloads, max_retries, metadata_delay_ms).

## Target State

A **photo sorter**: single `album_files` SQLite table, a `SorterService` that moves locally-synced files into album-named folders, SSE file-count progress, and a single `icloud_folder` setting.

---

## Work Items

| ID | Work Item | Files | Depends On | Parallelizable With |
|----|-----------|-------|------------|---------------------|
| W1 | Config + DB schema | `config.py`, `models/db.py` | — | W3 |
| W2 | State service rewrite | `services/state_service.py` | W1 | W3 |
| W3 | Schemas + Settings | `models/schemas.py`, `routers/settings.py` | — | W1 |
| W4 | iCloud metadata sync | `services/icloud_service.py`, `routers/albums.py` | W2, W3 | — |
| W5 | Sorter engine | `services/sorter_service.py` (new) | W2, W3 | W4 |
| W6 | Sort router + app wiring | `routers/sort.py` (new), `app.py`, delete download files | W3, W5 | — |
| W7 | Integration cleanup | All backend files | W4, W6 | — |

### Dependency Graph

```
W1 ──→ W2 ──→ W4 ──→ W7
              ↗      ↗
W3 ──→ W5 ──→ W6 ──┘
```

**Parallel batches:**
1. **Batch 1:** W1 + W3 (no dependencies, independent files)
2. **Batch 2:** W2 + W5 (after their respective deps land — but W2 needs W1, W5 needs W3)
3. **Batch 3:** W4 + W6 (after W2/W3/W5)
4. **Batch 4:** W7 (integration sweep)

---

## Subagent Strategy

### Subagent A — Foundation + Data Layer (W1 + W2)
**Files:** `backend/config.py`, `backend/models/db.py`, `backend/services/state_service.py`

### Subagent B — API Contracts + Settings (W3)
**Files:** `backend/models/schemas.py`, `backend/routers/settings.py`

*Subagents A and B run in parallel.*

### Subagent C — iCloud Metadata Sync (W4)
**Files:** `backend/services/icloud_service.py`, `backend/routers/albums.py`

### Subagent D — Sorter Engine (W5)
**Files:** `backend/services/sorter_service.py` (new)

*Subagents C and D run in parallel, after A and B complete.*

### Subagent E — Routing + Wiring + Cleanup (W6 + W7)
**Files:** `backend/routers/sort.py` (new), `backend/app.py`, delete `backend/routers/download.py`, delete `backend/services/download_service.py`

*Runs last, after C and D complete.*

---

## Detailed Specifications

### W1 — Config + DB Schema

#### `backend/config.py`
Replace all download constants:

```python
from pathlib import Path

APP_STATE_DIR: Path = Path.home() / ".icloud-sorter"
STATE_DB_PATH: Path = APP_STATE_DIR / "state.db"
COOKIE_DIR: Path = APP_STATE_DIR / "cookies"
SETTINGS_PATH: Path = APP_STATE_DIR / "settings.json"

DEFAULT_ICLOUD_FOLDER: str = ""
```

Remove: `DEFAULT_DOWNLOAD_PATH`, `DEFAULT_CONCURRENT_DOWNLOADS`, `DEFAULT_METADATA_DELAY_MS`, `DEFAULT_MAX_RETRIES`.

#### `backend/models/db.py`
Replace entire schema with:

```sql
CREATE TABLE IF NOT EXISTS album_files (
    album_id    TEXT NOT NULL,
    album_name  TEXT NOT NULL,
    filename    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    error       TEXT,
    PRIMARY KEY (album_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_album_files_status ON album_files(status);
CREATE INDEX IF NOT EXISTS idx_album_files_album ON album_files(album_id);
```

Keep `init_db()` and `get_db()` function signatures unchanged.

---

### W2 — State Service Rewrite

#### `backend/services/state_service.py`
Delete all download-related functions. **Keep `save_session()` and `get_session()`** — they are called by `icloud_service.login()` which is unchanged. The `sessions` table is gone from the new schema, so rewrite these two to use a JSON file (`~/.icloud-sorter/session.json`) instead of SQLite. Delete everything else. Implement:

```python
def replace_album_files(rows: list[dict[str, str]]) -> None
```
- Single transaction: `DELETE FROM album_files`, then batch-insert all rows with `status='pending'`, `error=NULL`.

```python
def get_album_summaries() -> list[dict[str, Any]]
```
- Returns per-album: `{id, name, asset_count, sorted_count, failed_count}`.
- SQL: `GROUP BY album_id, album_name ORDER BY LOWER(album_name), album_id`.

```python
def reset_album_files(album_ids: list[str]) -> None
```
- Set `status='pending'`, `error=NULL` for given album IDs.

```python
def get_pending_album_files(album_ids: list[str]) -> list[dict[str, str]]
```
- Returns `{album_id, album_name, filename}` where `status='pending'`.
- `ORDER BY LOWER(album_name), LOWER(filename)`.

```python
def mark_album_file_sorted(album_id: str, filename: str) -> None
```
- Set `status='sorted'`, `error=NULL`.

```python
def mark_album_file_failed(album_id: str, filename: str, error: str) -> None
```
- Set `status='failed'`, `error=<message>`.

---

### W3 — Schemas + Settings

#### `backend/models/schemas.py`
**Keep unchanged:** `ErrorResponse`, `LoginRequest`, `LoginResponse`, `TwoFactorRequest`, `TwoFactorResponse`, `SessionResponse`, `AlbumInfo`, `AlbumListResponse`.

**Remove:** `AssetInfo`, `AssetListResponse`, `DownloadError`, `DownloadStartRequest`, `DownloadStartResponse`, `DownloadProgressEvent`, `PauseResponse`, `CancelResponse`, and old `SettingsResponse` / `SettingsUpdateRequest`.

**Add:**
```python
class SortStartRequest(BaseModel):
    album_ids: list[str]

class SortStartResponse(BaseModel):
    total_files: int

class SortError(BaseModel):
    filename: str
    error: str
    album: str

class SortProgressEvent(BaseModel):
    status: str  # "sorting" | "complete" | "error"
    total_files: int
    completed_files: int
    failed_files: int
    current_file: str
    current_album: str
    errors: list[SortError]

class SettingsResponse(BaseModel):
    icloud_folder: str

class SettingsUpdateRequest(BaseModel):
    icloud_folder: Optional[str] = None
```

#### `backend/routers/settings.py`
- Import new config constants (`SETTINGS_PATH`, `DEFAULT_ICLOUD_FOLDER`) and new schema models.
- `_get_defaults()` returns `{"icloud_folder": DEFAULT_ICLOUD_FOLDER}`.
- Optional auto-detect: check `~/Pictures/iCloud Photos/Photos`, `~/iCloudPhotos`, `~/Pictures/iCloud Photos` — use the first that exists as default.
- GET/PUT endpoints unchanged in structure, just return `SettingsResponse`.

---

### W4 — iCloud Metadata Sync

#### `backend/services/icloud_service.py`
**Keep unchanged:** `login()`, `validate_2fa()`, `get_session_status()`, `_is_authenticated()`, `_sanitize_folder_name()`, module-level auth globals.

**Remove:** `AuthenticationError`, `get_album_assets()`, `get_album_by_id()`, `get_asset_from_album()`, `download_asset_data()`.

**Keep `get_albums()` lightweight** (current behavior: fetches album names + counts, no per-asset iteration). This is fast even for large libraries.

**Add `sync_album_metadata()`** — the heavy per-asset iteration happens here, called separately before sorting:
1. Check `_is_authenticated()`.
2. Iterate `photos.albums`:
   - Get `name`, `album_id` (same as current).
   - Iterate each album's assets and collect `filename` via `getattr(asset, "filename", None)`. Skip if blank.
   - Accumulate rows: `{album_id, album_name, filename}`.
3. Call `state_service.replace_album_files(rows)`.
4. Return row count for progress feedback.

**Rewrite `get_albums()`:**
1. Check `_is_authenticated()`.
2. Iterate `photos.albums` (same as current — name, id, `len(album)`).
3. Compute `folder_name` using `_compute_folder_names()` (shared helper, see below).
4. Call `state_service.save_albums(albums_list)` (keep current behavior).
5. Return album list matching `AlbumInfo` shape: `{id, name, asset_count, folder_name}`.

**Add shared helper `_compute_folder_names(albums: list[dict]) -> dict[str, str]`:**
- Input: list of `{id, name}` dicts.
- Sort by `(name.casefold(), id)` for deterministic ordering.
- Apply `_sanitize_folder_name()` + collision resolution (`Name (2)`, `Name (3)`, etc.).
- Return `{album_id: folder_name}` mapping.
- Used by both `get_albums()` and `sorter_service._run_sort()`.

#### `backend/routers/albums.py`
- Remove `/{album_id}/assets` endpoint and `AssetListResponse` import.
- Keep `GET /api/albums` — calls `icloud_service.get_albums()`, returns `AlbumListResponse`.

---

### W5 — Sorter Engine

#### `backend/services/sorter_service.py` (new file)

**Class: `SorterService`**

State:
- `_running: bool`, `_status: str` (idle/sorting/complete/error)
- `_total_files`, `_completed_files`, `_failed_files: int`
- `_current_file`, `_current_album: str`
- `_errors: list[dict]` — `{filename, error, album}`

**`start(album_ids) -> dict`:**
1. Guard: already running → `{error: "sort_in_progress"}`.
2. Guard: not authenticated → `{error: "not_authenticated"}`.
3. Load settings, get `icloud_folder`.
4. Validate folder exists → `{error: "file_not_found"}` if not.
5. `state_service.reset_album_files(album_ids)`.
6. `rows = state_service.get_pending_album_files(album_ids)`.
7. If empty → `{error: "not_found"}`.
8. Init progress, set `_running = True`, `_status = "sorting"`.
9. Schedule background: `asyncio.create_task(asyncio.to_thread(self._run_sort, rows, icloud_folder))` (called from inside an async endpoint, so the running loop is available).
10. Return `{total_files: len(rows)}`.

**`_run_sort(rows, icloud_folder)`:**
1. Build folder map: `album_id → folder_name` using `icloud_service._compute_folder_names()` (shared helper from W4 — ensures identical folder names as `get_albums()`).
2. Build file index: scan `icloud_folder` recursively, index `filename.casefold() → list[Path]`.
3. Track already-moved files (`set[Path]`) to enforce move-once for cross-album duplicates.
4. For each row:
   - Update `_current_file`, `_current_album`.
   - `target_dir = Path(icloud_folder) / folder_name`.
   - `target_dir.mkdir(parents=True, exist_ok=True)`.
   - Find candidates by `filename.casefold()` in file index.
   - **Already in target_dir?** → mark sorted (no move needed).
   - **In root or elsewhere?** → move with collision suffix: `IMG_0001 (2).JPG`.
   - **Already claimed by another album?** → mark failed `"Already moved to another album"`.
   - **Not found?** → mark failed `"File not found"`.
   - Use `os.rename()` / `Path.rename()` for moves.
   - Catch `PermissionError`, `OSError` → mark failed.
5. Set `_status = "complete"`, `_running = False`.
6. Wrap entire loop in try/except for fatal errors → `_status = "error"`.

**`get_progress() -> dict`:**
Return current state matching `SortProgressEvent` shape.

**`is_running() -> bool`:**
Return `_running`.

**Module-level singleton:**
```python
sorter_service = SorterService()
```

---

### W6 — Sort Router + App Wiring

#### `backend/routers/sort.py` (new file)
```python
POST /api/sort/start
```
- Accept `SortStartRequest`, call `sorter_service.start(request.album_ids)`.
- Error status map: `sort_in_progress` → 409, `not_authenticated` → 401, `not_found` → 404, `file_not_found` → 400, `permission_denied` → 403, else → 500.
- Success → `SortStartResponse`.

```python
GET /api/sort/progress
```
- SSE stream modeled on current `download.py`.
- Poll `sorter_service.get_progress()` every 0.5s.
- Stop when `status in ("complete", "error")`.

#### `backend/app.py`
- Change imports: `from backend.routers import auth, albums, sort, settings`.
- Replace `download.router` with `sort.router`.
- Update app title to `"iCloud Photo Sorter"`.

#### Delete files
- `backend/routers/download.py` (exists: `routers/download.py`)
- `backend/services/download_service.py` (exists: `services/download_service.py`)

---

### W7 — Integration Cleanup

Grep backend for stale references:
- `download`, `downloads`, `assets`, `album_assets`, `DEFAULT_DOWNLOAD_PATH`
- `concurrent_downloads`, `metadata_delay_ms`, `max_retries`
- `PauseResponse`, `CancelResponse`, `AssetListResponse`, `DownloadError`

Every hit must be intentional or removed.

**Smoke-test checklist:**
1. `python backend/app.py` starts without errors
2. `GET /api/settings` → `{"icloud_folder": "..."}`
3. `PUT /api/settings` → round-trips `icloud_folder`
4. `GET /api/auth/session` → works
5. `GET /api/albums` → returns album list, populates `album_files` table
6. `POST /api/sort/start` → returns `{total_files}`, starts background job
7. `GET /api/sort/progress` → streams SSE events
8. Files are moved into album folders; DB statuses updated

---

## Testing

No frontend in Phase 1 — test via curl. Start the backend first:

```bash
cd /home/mac/code/sorter
python backend/app.py
```

### Step 1: Configure iCloud folder

```bash
# Set your local iCloud Photos folder
curl -s -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"icloud_folder": "/path/to/your/iCloud Photos/Photos"}' | python -m json.tool

# Verify it saved
curl -s http://localhost:8000/api/settings | python -m json.tool
```

### Step 2: Authenticate

```bash
# Login
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"apple_id": "your@apple.id", "password": "your-password"}' | python -m json.tool

# If requires_2fa is true, submit the code:
curl -s -X POST http://localhost:8000/api/auth/2fa \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}' | python -m json.tool

# Verify session
curl -s http://localhost:8000/api/auth/session | python -m json.tool
```

### Step 3: Fetch albums

```bash
# This populates the album_files table and returns album list
curl -s http://localhost:8000/api/albums | python -m json.tool
```

Note the album `id` values from the response — you'll need them for sorting.

### Step 4: Start sort

```bash
# Sort one or more albums (use real IDs from step 3)
curl -s -X POST http://localhost:8000/api/sort/start \
  -H "Content-Type: application/json" \
  -d '{"album_ids": ["ALBUM_ID_1", "ALBUM_ID_2"]}' | python -m json.tool
```

### Step 5: Watch progress (SSE)

```bash
# Stream progress events (Ctrl+C to stop)
curl -N http://localhost:8000/api/sort/progress
```

### Step 6: Verify results

```bash
# Check the filesystem — album folders should exist with files inside
ls -la "/path/to/your/iCloud Photos/Photos/"

# Check the database
sqlite3 ~/.icloud-sorter/state.db "SELECT album_name, status, COUNT(*) FROM album_files GROUP BY album_name, status;"

# Check for failures
sqlite3 ~/.icloud-sorter/state.db "SELECT album_name, filename, error FROM album_files WHERE status='failed';"
```

### Quick smoke test (no iCloud auth needed)

To verify the backend starts and APIs respond without needing real credentials.
**Note:** Uses background process (`&` / `kill %1`) — interactive shell only. For CI, use a process manager or `timeout`.

```bash
# Backend starts without error
python backend/app.py &
sleep 2

# Settings round-trip
curl -s http://localhost:8000/api/settings | python -m json.tool
curl -s -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"icloud_folder": "/tmp/test-icloud"}' | python -m json.tool

# Session returns unauthenticated
curl -s http://localhost:8000/api/auth/session | python -m json.tool

# Albums rejects when not authenticated (expect 401)
curl -s -w "\nHTTP %{http_code}\n" http://localhost:8000/api/albums

# Sort rejects when not authenticated (expect 401)
curl -s -w "\nHTTP %{http_code}\n" -X POST http://localhost:8000/api/sort/start \
  -H "Content-Type: application/json" \
  -d '{"album_ids": ["test"]}'

kill %1
```

---

## Design Decisions for Phase 1

| Decision | Choice | Rationale |
|----------|--------|-----------|
| DB migration | New DB path (`~/.icloud-sorter/`) | Avoids drop-table complexity; clean slate |
| Metadata refresh | Destructive replace (`DELETE` + `INSERT`) | Simplest; resets sort status which is fine for MVP |
| Cross-album duplicates | Move to first album, skip subsequent | Per planning doc; tracked via file index |
| Pause/Resume/Cancel | Not implemented | Not needed for instant file moves |
| Folder name computation | Global deterministic (all albums, sorted) | Prevents name drift between runs |
| Background execution | Sequential single-threaded | File moves are instant; no concurrency needed |
| Sort completion status | `complete` even if some files failed | Per-file errors reported separately |
