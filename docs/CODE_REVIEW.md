# Code Review — Phase 2 (Download Engine)

Reviewed: 2026-02-26  
Scope: `backend/services/download_service.py`, `backend/services/icloud_service.py`, `backend/routers/download.py`, `backend/services/state_service.py`, `frontend/src/components/DownloadProgress.tsx`, `frontend/src/components/AlbumBrowser.tsx`, `frontend/src/App.tsx`, `frontend/src/hooks/useApi.ts`

## How to use this file

- Mark issues as fixed by changing `[ ]` to `[x]` and adding a note.
- Remove an issue entirely once verified in a follow-up review.

---

## Open Issues

### 1. HIGH — Serialized downloads negate thread pool concurrency
**File:** `backend/services/download_service.py:189`

`await loop.run_in_executor(self._executor, self._download_one, record)` inside the `for` loop blocks on each download before starting the next, making all downloads serial regardless of `max_workers` / `concurrent_downloads`.

**Fix:** Use `asyncio.Semaphore` or maintain a set of active futures with `asyncio.wait(return_when=FIRST_COMPLETED)` to allow up to `concurrent_downloads` tasks in parallel.

- [x] Fixed — Replaced serial `for` loop with `asyncio.Semaphore` + `asyncio.gather` to run up to `concurrent_downloads` tasks in parallel.

---

### 2. HIGH — Auth errors swallowed in `download_asset_data`
**File:** `backend/services/icloud_service.py:256`

The bare `except Exception` catches auth errors (HTTP 401/403) and returns `None`, making them indistinguishable from network errors. The download service then retries until `max_retries` is exhausted instead of emitting `session_expired` via SSE as required by the API contract.

**Fix:** Catch `PyiCloudAPIResponseError` (or equivalent auth exceptions) separately and re-raise them, or return a distinguishable error type that `download_service._download_one` can detect to trigger the `session_expired` SSE event.

- [x] Fixed — `download_asset_data` now catches `PyiCloudFailedLoginException` and `PyiCloudAPIResponseException` with code 401/403 separately, raising `AuthenticationError`.

---

### 3. MEDIUM — No auth error handling in download worker
**File:** `backend/services/download_service.py:332-335`

Depends on issue #2. Once `icloud_service.download_asset_data` surfaces auth errors distinctly, `_download_one` needs logic to detect them and set the download status to `"error"` with `session_expired` rather than retrying.

- [x] Fixed — `_download_one` now catches `AuthenticationError`, sets status to `"error"` with `session_expired`, cancels remaining downloads, and includes `error`/`message` in SSE progress.

---

### 4. MEDIUM — Disk check counters read without lock
**File:** `backend/services/download_service.py:195-196`

`self._files_since_disk_check` and `self._bytes_since_disk_check` are read outside `self._lock` in the main loop, but written under the lock in worker threads (lines 286, 371). This is a race condition.

**Fix:** Wrap the read in `with self._lock:`.

- [x] Fixed — Counter increment and read now happen together inside `with self._lock:` in `_download_task`.

---

### 5. MEDIUM — `get_album_assets` called with limit=99999
**File:** `backend/services/download_service.py:105`

If the underlying iCloud API paginates internally, a single call with `limit=99999` may be silently truncated, leading to incomplete downloads for large albums.

**Fix:** Verify that `icloud_service.get_album_assets` iterates all pages internally, or loop with pagination in `download_service.start()`.

- [x] Fixed — `start()` now loops with `page_size=200` pagination instead of a single `limit=99999` call.

---

## Resolved Issues

_(Move issues here after fixing and verifying.)_
