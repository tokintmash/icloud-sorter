# iCloud Photo Downloader — MVP Planning Document

*February 2026 — School Project / Simplified Architecture*

---
## What Is This?

iCloud Photo Downloader is an application that lets you download your photos from iCloud by albums without the need of having a Mac. You pick the albums you want, and the app downloads them. No Mac needed.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technology Stack](#2-technology-stack)
3. [iCloud API Approach](#3-icloud-api-approach)
4. [Architecture](#4-architecture)
5. [Data Model & State Management](#5-data-model--state-management)
6. [Media Type Handling](#6-media-type-handling)
7. [Filename & Deduplication Strategy](#7-filename--deduplication-strategy)
8. [Download Pipeline](#8-download-pipeline)
9. [Project Structure](#9-project-structure)
10. [Distribution](#10-distribution)
11. [Risk Assessment](#11-risk-assessment)
12. [Implementation Phases](#12-implementation-phases)

---

## 1. Executive Summary

### Approach: Python Backend + React Frontend (No Go, No Binary)

**Stack:** Python (FastAPI) backend using `pyicloud` directly, React/TypeScript frontend (Vite), SQLite for state management.

**Rationale:**
- **Simplicity:** Two languages instead of three. No subprocess bridge, no Go, no binary compilation
- **pyicloud is used directly:** No JSON-RPC bridge needed — Python calls pyicloud natively
- **Zero cost:** No code signing, no developer accounts, no packaging infrastructure
- **Distribution:** Users clone the repo and run it locally. Ideal for a school project
- **Team fit:** Team knows JavaScript and has some Python experience; this stack uses both

### What Changed From the Full Plan

| Full Plan | MVP |
|-----------|-----|
| Go (Wails) + Python subprocess + React | Python (FastAPI) + React |
| Compiled binary with installer | Clone repo + run locally |
| Code signing + notarization ($350/year) | Not needed |
| JSON-RPC bridge between Go and Python | pyicloud called directly in Python |
| Go goroutines for concurrency | Python `asyncio` + `ThreadPoolExecutor` |
| `go-keyring` for OS keychain | pyicloud's built-in cookie persistence |

---

## 2. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend** | Python 3.10+ with FastAPI | Async-capable, auto-generates OpenAPI docs, lightweight |
| **iCloud API** | `pyicloud` v2.x (timlaing fork) | Only actively maintained iCloud library with SRP, 2FA, Photos API — called directly, no bridge |
| **Frontend** | React + TypeScript (Vite) | Team knows JS; rich ecosystem for progress UIs |
| **State DB** | SQLite (Python `sqlite3` stdlib) | Zero setup, embedded, no external dependencies |
| **Concurrency** | `asyncio` + `ThreadPoolExecutor` | Async HTTP serving + threaded downloads (pyicloud is synchronous) |
| **Build** | pip + npm/pnpm | Standard tooling, no compilation step |

### Why FastAPI Over Flask

- Native async support (important for SSE/WebSocket progress updates)
- Auto-generated API docs at `/docs` (useful for development/debugging)
- Built-in request validation via Pydantic
- Modern Python patterns

---

## 3. iCloud API Approach

### Library: pyicloud v2.x (timlaing/pyicloud)

| Attribute | Value |
|-----------|-------|
| **PyPI Package** | `pyicloud` v2.3.0 (Jan 2026) |
| **Auth** | SRP-6a, 2FA (trusted device, SMS, FIDO2), session persistence |
| **Photos API** | Album listing, asset iteration with pagination, original/medium/thumb/adjusted downloads |
| **Session Lifetime** | ~2 months, then re-auth with 2FA required |
| **License** | MIT |

### What the API Provides

- **Albums:** User-created albums + "All Photos". NOT shared albums, smart albums, or Recently Deleted
- **Per asset:** ID, filename, size, dimensions, creation date, versions (original/medium/thumb/adjusted)
- **Download:** Pre-signed, time-limited CDN URLs via `photo.download(version)`
- **Pagination:** Cursor-based, ~200 records/page, handled transparently by pyicloud

### User Prerequisites (Must Document Prominently)

1. **Enable** "Access iCloud Data on the Web" in iOS Settings → Apple ID → iCloud
2. **Disable** Advanced Data Protection (ADP) — Apple returns `ACCESS_DENIED` otherwise
3. Accept any pending iCloud Terms of Service

### Rate Limiting Strategy

| Parameter | Default | Configurable |
|-----------|---------|-------------|
| Concurrent downloads | 3 | Yes (1–10) |
| Delay between metadata API calls | 200ms | Yes |
| Retry on 503 | Exponential backoff starting at 30s | Yes |
| Max retries per asset | 3 | Yes |

---

## 4. Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript, served by FastAPI)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Auth     │ │  Album   │ │ Download │ │  Settings     │  │
│  │  Screen   │ │  Browser │ │ Progress │ │  (paths,      │  │
│  │  (2FA)    │ │  (select)│ │ (live)   │ │   concurrency)│  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │ REST API + SSE (Server-Sent Events)
┌─────────────────────────────────────────────────────────────┐
│  PYTHON BACKEND (FastAPI)                                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  AuthRouter   │  │ AlbumRouter  │  │  DownloadRouter    │ │
│  │  POST /login  │  │ GET /albums  │  │  POST /download    │ │
│  │  POST /2fa    │  │ GET /albums/ │  │  GET  /progress    │ │
│  │  GET /session │  │   /:id/assets│  │  POST /pause       │ │
│  └──────┬───────┘  └──────┬───────┘  │  POST /cancel      │ │
│         │                  │          └──────────┬─────────┘ │
│         ▼                  ▼                     │           │
│  ┌─────────────────────────────────────┐         │           │
│  │  iCloudService                      │◄────────┘           │
│  │  (pyicloud directly — no bridge)    │                     │
│  │  - PyiCloudService instance         │                     │
│  │  - Auth, albums, asset metadata     │                     │
│  │  - Download streaming               │                     │
│  └─────────────────────────────────────┘                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────────────────────────────┐  │
│  │  StateDB      │  │  DownloadWorker                     │  │
│  │  (SQLite)     │  │  (ThreadPoolExecutor, max_workers=3)│  │
│  └──────────────┘  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Login with Apple ID + password |
| `POST` | `/api/auth/2fa` | Submit 2FA code |
| `GET` | `/api/auth/session` | Check session status |
| `GET` | `/api/albums` | List all albums with asset counts |
| `GET` | `/api/albums/:id/assets` | List assets in an album (paginated) |
| `POST` | `/api/download/start` | Start downloading selected albums |
| `GET` | `/api/download/progress` | SSE stream of download progress |
| `POST` | `/api/download/pause` | Pause downloads |
| `POST` | `/api/download/cancel` | Cancel downloads |
| `GET` | `/api/settings` | Get current settings |
| `PUT` | `/api/settings` | Update settings |

### Concurrency Model

Since pyicloud is synchronous (uses `requests` internally), downloads run in a `ThreadPoolExecutor`:

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

class DownloadService:
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.paused = False
        self.cancelled = False

    async def download_albums(self, albums: list[str]):
        loop = asyncio.get_event_loop()
        for job in self.pending_jobs():
            if self.cancelled:
                break
            while self.paused:
                await asyncio.sleep(0.5)
            await loop.run_in_executor(
                self.executor, self.download_one, job
            )
```

### Progress Updates via SSE

Server-Sent Events (SSE) push real-time progress to the frontend without WebSocket complexity:

```python
@router.get("/api/download/progress")
async def progress_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            progress = download_service.get_progress()
            yield f"data: {json.dumps(progress)}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Error Handling & Retry Strategy

| Error Type | Action |
|-----------|--------|
| HTTP 503 (throttled) | Retry with exponential backoff; honor `retryAfter` header |
| HTTP 401/403 (auth expired) | Re-authenticate; if 2FA needed, prompt user via frontend |
| Network timeout | Retry up to 3 times with backoff |
| Disk write error | Fail the asset, log error, continue with next |
| Disk space exhausted | Pause all downloads, alert user |

---

## 5. Data Model & State Management

### SQLite Schema

```sql
-- Track iCloud sessions
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY,
    apple_id    TEXT NOT NULL,
    cookie_dir  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT,
    last_used   TEXT NOT NULL
);

-- Albums discovered from iCloud
CREATE TABLE albums (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    asset_count     INTEGER,
    last_synced_at  TEXT,
    folder_name     TEXT NOT NULL
);

-- Assets (photos/videos) in iCloud
CREATE TABLE assets (
    id              TEXT PRIMARY KEY,
    filename        TEXT NOT NULL,
    size_bytes      INTEGER,
    item_type       TEXT,
    created_at      TEXT,
    has_adjustments INTEGER DEFAULT 0,
    width           INTEGER,
    height          INTEGER
);

-- Junction: which assets belong to which albums
CREATE TABLE album_assets (
    album_id    TEXT NOT NULL REFERENCES albums(id),
    asset_id    TEXT NOT NULL REFERENCES assets(id),
    position    INTEGER,
    PRIMARY KEY (album_id, asset_id)
);

-- Download tracking
CREATE TABLE downloads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    album_id        TEXT NOT NULL REFERENCES albums(id),
    version         TEXT NOT NULL,
    local_path      TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
                    -- 'pending', 'downloading', 'complete', 'failed', 'skipped'
    file_size       INTEGER,
    bytes_downloaded INTEGER DEFAULT 0,
    error_message   TEXT,
    attempts        INTEGER DEFAULT 0,
    started_at      TEXT,
    completed_at    TEXT,
    UNIQUE(asset_id, album_id, version)
);

CREATE INDEX idx_downloads_status ON downloads(status);
CREATE INDEX idx_downloads_album ON downloads(album_id, status);
CREATE INDEX idx_album_assets_album ON album_assets(album_id);
```

### Deduplication Key

**Primary key:** iCloud asset ID (CloudKit record name) — globally unique, stable across sessions.

**Incremental sync logic:**
1. Query iCloud for album assets (paginated)
2. For each asset, check `downloads` table: if `status = 'complete'` AND `file_size` matches, skip
3. If `status = 'failed'` and `attempts < max_retries`, retry
4. If asset not in DB, insert as `pending`

### State DB Location

`~/.icloud-downloader/state.db` — separate from the download directory so users can move/change download locations without losing state.

---

## 6. Media Type Handling

### Policy Summary (MVP)

| Media Type | Policy | Naming |
|-----------|--------|--------|
| **JPEG/PNG** | Download original | `IMG_1234.JPG` |
| **HEIC** | Download original (no conversion in MVP) | `IMG_1234.HEIC` |
| **Live Photos** | Download both image + video | `IMG_1234.HEIC` + `IMG_1234.MOV` |
| **Videos** | Download as-is | Original filename |
| **Edited photos** | Download original only (MVP) | `IMG_1234.HEIC` |
| **RAW+JPEG** | Download both files | `IMG_1234.DNG` + `IMG_1234.JPG` |
| **Bursts** | All frames (MVP — key photo detection is unreliable via web API) | Standard naming per frame |

### Album Scope

| Album Type | In Scope | Notes |
|-----------|----------|-------|
| **User-created albums** | ✅ Yes | Core feature |
| **"All Photos"** | ✅ Yes | As a special album option |
| **Shared Albums** | ❌ No | Different API, not supported by pyicloud |
| **Smart Albums** | ⚠️ Partial | Include if pyicloud exposes them |
| **Recently Deleted** | ❌ No | Not exposed via web API |

---

## 7. Filename & Deduplication Strategy

### Collision Resolution (Within Album Folder)

**Strategy: Append date, then sequence number on further collision.**

```
IMG_0001.HEIC                    ← first occurrence
IMG_0001_2024-03-15.HEIC         ← second, different asset, append EXIF date
IMG_0001_2024-03-15 (2).HEIC     ← third, same date collision, append sequence
IMG_0001_2024-07-22.HEIC         ← fourth, different date
```

### Cross-Album Duplicates

**Strategy: Download the file into each album folder independently.**

**Optimization:** If the same `asset_id + version` already exists locally with `status = 'complete'`, **copy the local file** instead of re-downloading from iCloud.

### Filesystem Name Sanitization

Album names → folder names:
```
1. Replace characters invalid on any OS: / \ : * ? " < > |  → _
2. Trim leading/trailing whitespace and dots
3. Truncate to 200 characters
4. If empty after sanitization, use "Unnamed Album"
5. If folder name collides, append " (2)", " (3)", etc.
```

---

## 8. Download Pipeline

### Atomic Writes

```
1. Create temp file: <album_folder>/.IMG_1234.HEIC.tmp
2. Stream download data to temp file
3. On completion: verify size matches expected
4. Rename: .IMG_1234.HEIC.tmp → IMG_1234.HEIC (atomic on same filesystem)
5. Update downloads table: status = 'complete'
```

On app startup, any leftover `.tmp` files are deleted (interrupted downloads).

### Resume Support

**Policy:** No partial file resume in MVP. Delete `.tmp` files on restart and re-download. Individual photos are typically 2–10 MB (seconds to re-download). Already-completed files are skipped via the `downloads` table.

### Pause / Cancel

| Action | Behavior |
|--------|----------|
| **Pause** | Set `paused` flag. Workers finish current file, then wait. |
| **Resume** | Clear `paused` flag. Workers continue from where they left off. |
| **Cancel** | Set `cancelled` flag. Workers finish current file, then stop. Delete any `.tmp` files. Mark remaining `pending` as `skipped`. |

### Disk Space Checking

```
1. Before starting: sum expected sizes of all pending downloads
2. Check available disk space via shutil.disk_usage()
3. If insufficient: return error to frontend with required vs available space
4. During download: re-check every 100 files or 1 GB downloaded
5. If space runs low (<500 MB remaining): pause downloads, alert user
```

---

## 9. Project Structure

```
icloud-downloader/
├── backend/
│   ├── app.py                  # FastAPI app entry point
│   ├── requirements.txt        # pyicloud, fastapi, uvicorn, etc.
│   ├── routers/
│   │   ├── auth.py             # /api/auth/* endpoints
│   │   ├── albums.py           # /api/albums/* endpoints
│   │   ├── download.py         # /api/download/* endpoints
│   │   └── settings.py         # /api/settings endpoints
│   ├── services/
│   │   ├── icloud_service.py   # pyicloud wrapper (auth, albums, assets)
│   │   ├── download_service.py # Download worker pool, progress tracking
│   │   └── state_service.py    # SQLite state management
│   ├── models/
│   │   ├── schemas.py          # Pydantic models for API request/response
│   │   └── db.py               # SQLite schema + queries
│   └── config.py               # App configuration (paths, defaults)
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── AuthScreen.tsx
│       │   ├── AlbumBrowser.tsx
│       │   ├── DownloadProgress.tsx
│       │   └── Settings.tsx
│       ├── hooks/
│       │   └── useApi.ts       # API client hooks
│       ├── types/
│       │   └── api.ts          # TypeScript types matching Pydantic schemas
│       └── styles/
│
├── docs/
│   ├── PREREQUISITES.md        # User setup guide (iCloud settings)
│   └── DEVELOPMENT.md          # Developer setup guide
│
├── LICENSE                     # MIT
├── README.md
├── DISCLAIMER.md               # Apple TOS disclaimer
├── PLANNING.md                 # Full plan (reference)
└── PLANNING_MVP.md             # This document
```

---

## 10. Distribution

### No Binary, No Signing

This is a **clone-and-run** project. No compiled binary, no installer, no code signing costs.

### User Setup

```bash
# Clone
git clone https://github.com/<org>/icloud-downloader.git
cd icloud-downloader

# Backend
cd backend
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build                   # builds static files to dist/

# Run
cd ../backend
python app.py                   # serves API + frontend on http://localhost:8000
```

### Prerequisites for Users

1. **Python 3.10+** installed
2. **Node.js 18+** installed (for building frontend; not needed at runtime)
3. **iCloud settings:**
   - Enable "Access iCloud Data on the Web" in iOS Settings → Apple ID → iCloud
   - Disable Advanced Data Protection
   - Accept any pending Terms of Service

### Cost

| Item | Cost |
|------|------|
| Everything | **$0** |

---

## 11. Risk Assessment

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|------------|
| 1 | **Apple changes auth endpoints** | 🔴 High | Near-certain (1–2x/year) | pyicloud community fixes within days–weeks. Pin version, update when needed. |
| 2 | **Rate limiting / throttling** | 🟡 Medium | Likely for large libraries | Conservative defaults (3 concurrent, backoff); honor 503 retryAfter |
| 3 | **pyicloud ecosystem stagnation** | 🟡 Medium | Medium | We depend on pyicloud directly; monitor and update |
| 4 | **Session expiry (every ~2 months)** | 🟢 Low | Certain | Clear UX for re-authentication; cookie persistence |
| 5 | **Python version issues on user machines** | 🟡 Medium | Medium | Document Python 3.10+ requirement clearly; consider Docker as alternative |

### Removed Risks (vs Full Plan)

These risks from the full plan no longer apply:

- ~~Python bundling complexity~~ — users install Python themselves
- ~~Wails v2 → v3 migration~~ — no Wails
- ~~Code signing costs~~ — no binary distribution
- ~~Go↔Python bridge crashes~~ — no bridge, pyicloud called directly

---

## 12. Implementation Phases

### Phase 1: Auth + Album Listing (Week 1–2)

**Goal:** Login to iCloud and see a list of albums in the browser.

- [ ] Scaffold FastAPI backend + React (Vite) frontend
- [ ] Implement `icloud_service.py` — login, 2FA, session persistence using pyicloud
- [ ] Implement auth API endpoints (`/api/auth/login`, `/api/auth/2fa`, `/api/auth/session`)
- [ ] Implement album listing endpoint (`/api/albums`)
- [ ] Build Auth screen (Apple ID, password, 2FA code entry)
- [ ] Build Album browser (list albums with photo counts)
- [ ] Set up SQLite schema

### Phase 2: Download Engine (Week 3–4)

**Goal:** Download selected albums with progress tracking.

- [ ] Implement `download_service.py` — ThreadPoolExecutor worker pool
- [ ] Atomic writes (temp → rename)
- [ ] Filename collision resolution
- [ ] Cross-album file copy optimization
- [ ] SSE progress streaming (`/api/download/progress`)
- [ ] Build Download Progress screen (progress bars, speed, ETA)
- [ ] Disk space checking
- [ ] Pause / Cancel support

### Phase 3: Polish (Week 5–6)

**Goal:** Handle edge cases, improve UX.

- [ ] Retry logic with exponential backoff
- [ ] Handle auth re-prompts (session expired mid-download)
- [ ] Settings persistence (download path, concurrency)
- [ ] Error reporting UI (per-file errors with retry)
- [ ] Logging (file-based, viewable in UI)
- [ ] README with setup instructions + prerequisites
- [ ] Testing with real iCloud libraries

---

*This MVP plan prioritizes simplicity and zero cost. The full plan (PLANNING.md) can be revisited if the project needs to evolve into a distributable binary.*
