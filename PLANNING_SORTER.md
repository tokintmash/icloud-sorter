# PLANNING: iCloud Photo Sorter — MVP

## 1. Problem Statement

iCloud for Windows syncs all photos into a **flat folder** (`C:\Users\<user>\Pictures\iCloud Photos\`) with no album structure. Users lose their carefully curated album organization. This app reads iCloud album metadata via the API, matches it to locally synced files, and **organizes them into album-named folders** — no downloading required.

## 2. Architecture Overview

```
┌─ iPhone ──┐      ┌─ iCloud ──────────────┐
│  Photos   │─────▶│  Photo Library        │
│  Albums   │      │  (Albums + Images)    │
└───────────┘      └───────┬───────┬───────┘
                           │       │
              Syncs files  │       │  Album & image
              (flat)       │       │  metadata via API
                           ▼       ▼
┌─ Windows PC ─────────────────────────────────────────┐
│                                                       │
│  ┌─ Prerequisite ──────────┐  ┌─ Desktop App ──────┐ │
│  │ iCloud for Windows      │  │                     │ │
│  │                         │  │  pyicloud           │ │
│  │ C:\...\iCloud Photos\   │  │  (auth + metadata)  │ │
│  │  IMG_001.jpg            │  │        │            │ │
│  │  IMG_002.heic           │  │        ▼            │ │
│  │  IMG_003.mov            │  │  Album/File UI      │ │
│  │  ...flat, no albums     │  │        │            │ │
│  └──────────┬──────────────┘  │        ▼            │ │
│             │                 │  File Sorter Engine  │ │
│             │ Source files    │        │            │ │
│             └─────────────────┤        │            │ │
│                               └────────┼────────────┘ │
│                                        ▼              │
│  ┌─ Organized Output ────────────────────────────┐    │
│  │  📁 Vacation 2025/  photo1.jpg, photo2.jpg    │    │
│  │  📁 Family/         photo3.jpg, photo4.jpg    │    │
│  │  📁 Pets/           photo5.jpg                │    │
│  └───────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

## 3. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Desktop framework** | **Electron** (or **Tauri v2**) | Real Windows app (.exe), auto-update, tray icon, native file dialogs. Needed for commercial distribution + licensing. |
| **Frontend** | React + TypeScript + Vite | Already built, reuse existing code. Bundled inside Electron. |
| **Backend / Main process** | Python (FastAPI + uvicorn) | Keeps pyicloud in-process. Electron spawns Python as a child process. |
| **iCloud API** | `pyicloud` (timlaing fork) | Only maintained library for iCloud auth + Photos API. |
| **State DB** | SQLite (`sqlite3` stdlib) | Track metadata cache, sort operations, file mappings. |
| **Installer** | electron-builder / NSIS | Windows `.exe` installer with code signing. |
| **Auto-update** | electron-updater | GitHub Releases or custom update server. |
| **Licensing** | Keygen.sh / Gumroad / LemonSqueezy | License key validation on app startup. API-based verification. |
| **Website** | Static site (Astro / Next.js / simple HTML) | Landing page + purchase flow. Hosted on Vercel/Netlify. |
| **CI/CD** | GitHub Actions | Build, sign, release `.exe`. Publish website. |

### Stack Decision: Electron vs Tauri

| Factor | Electron | Tauri v2 |
|--------|---------|---------|
| Bundle size | ~80-120 MB | ~8-15 MB |
| Windows .exe | ✅ Mature | ✅ Supported |
| Auto-update | ✅ Built-in | ✅ Built-in |
| Python subprocess | ✅ Easy (Node child_process) | ✅ Possible (Rust sidecar) |
| Ecosystem/docs | ✅ Huge | 🟡 Growing |
| Code signing | ✅ Mature | ✅ Supported |
| Vibe-coding friendly | ✅ More JS, easier to iterate | 🟡 Rust can slow iteration |

**Recommendation:** Start with **Electron** for fastest iteration. Migrate to Tauri later if bundle size matters.

### Alternative: No Electron — Pure Web (Current Architecture)

If commercial packaging isn't a priority for MVP:
- Keep FastAPI + React served locally (current architecture)
- Package with **PyInstaller** or **cx_Freeze** for a single `.exe`
- Loses native auto-update but is simpler

## 4. Core Data Flow

```
1. User launches app → license check
2. User authenticates with Apple ID (pyicloud: SRP + 2FA)
3. App fetches album list + filenames from iCloud API
4. App stores { album_id, album_name, filename } rows in SQLite
5. User sees album list with file counts, picks albums to sort
6. Sorter engine runs:
   - Creates album-named subfolders inside the iCloud Photos folder
   - Moves each file into its album folder
   - Updates status in SQLite (sorted / failed)
   - Reports progress via SSE
7. User sees completion summary
```

**Key simplification:** Files are moved *within* the iCloud Photos folder — no separate output folder. The iCloud Photos folder goes from flat to organized. Moving within the same drive is instant (rename, not copy).

## 5. File Matching Strategy

The critical challenge: matching iCloud asset metadata to local files synced by iCloud for Windows.

### Primary: Filename Match
- `asset.filename` from pyicloud → search in source folder
- Case-insensitive (Windows NTFS is case-insensitive)
- Handle both `IMG_1234.HEIC` and `IMG_1234.heic`

### Fallback: Filename + Size
- If multiple files share a name (unlikely but possible after user renames), use `asset.size` as a tiebreaker

### Edge Cases
| Scenario | Strategy |
|----------|----------|
| File exists in iCloud but not locally | Skip + report as "not synced yet" |
| File exists locally but not in any album | Optionally move to "Unsorted" folder |
| Live Photos (IMG_1234.HEIC + IMG_1234.MOV) | Match both files, keep together in album folder |
| Edited photos | iCloud for Windows syncs originals; match by original filename |
| RAW+JPEG pairs | Match both files (same base name, different extension) |
| Filename modified locally by user | Cannot match — report as unmatched |

### iCloud for Windows Folder Discovery
- Default path: `C:\Users\<username>\Pictures\iCloud Photos\Photos\`
- Alternative: `C:\Users\<username>\iCloudPhotos\`
- Registry key: `HKCU\Software\Apple Inc.\iCloud\` may contain the path
- Fallback: user manually selects folder via native file picker

## 6. SQLite Schema

Location: `~/.icloud-sorter/state.db`

**One table.** Album metadata and sort status are tracked together. The iCloud Photos source folder is a single known path (configured once in settings), so no per-file path tracking is needed.

```sql
CREATE TABLE album_files (
    album_id    TEXT NOT NULL,
    album_name  TEXT NOT NULL,       -- denormalized for simplicity
    filename    TEXT NOT NULL,
    status      TEXT DEFAULT 'pending',  -- 'pending', 'sorted', 'failed'
    error       TEXT,                    -- error message if failed
    PRIMARY KEY (album_id, filename)
);

CREATE INDEX idx_album_files_status ON album_files(status);
```

**Queries this supports:**

```sql
-- Album list with counts (what the user sees)
SELECT album_id, album_name, COUNT(*) as total,
       SUM(CASE WHEN status = 'sorted' THEN 1 ELSE 0 END) as sorted,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM album_files GROUP BY album_id, album_name;

-- Files to sort for selected albums
SELECT * FROM album_files WHERE album_id IN (?, ?) AND status = 'pending';

-- Mark file as sorted
UPDATE album_files SET status = 'sorted' WHERE album_id = ? AND filename = ?;

-- Reset an album for re-sort
UPDATE album_files SET status = 'pending', error = NULL WHERE album_id = ?;

-- Full re-sync: just DELETE all + re-insert from iCloud metadata
```

**Why one table works:**
- The source folder is always the same (iCloud Photos folder) — no per-file source path needed
- Users don't need detailed asset metadata (size, dimensions, type) — they just pick albums
- Album name is denormalized (repeated per row) but the trade-off is zero JOINs and trivial queries
- Sort status is per-file-per-album, which is the only state that matters
- To refresh metadata: `DELETE FROM album_files` → re-populate from iCloud API

## 7. API Contract

### Auth Endpoints (unchanged from current)

**`POST /api/auth/login`**
- Request: `{ "apple_id": string, "password": string }`
- Response: `{ "authenticated": true, "requires_2fa": false }` or `{ "authenticated": false, "requires_2fa": true }`

**`POST /api/auth/2fa`**
- Request: `{ "code": string }`
- Response: `{ "authenticated": true }`

**`GET /api/auth/session`**
- Response: `{ "authenticated": boolean, "apple_id": string | null, "requires_2fa": boolean }`

### Album Endpoints (unchanged)

**`GET /api/albums`**
- Response: `{ "albums": [{ "id": string, "name": string, "asset_count": number, "folder_name": string }] }`

**`GET /api/albums/:id/assets`**
- Query: `offset`, `limit`
- Response: `{ "assets": [...], "total": number, "offset": number, "limit": number }`

### Sort Endpoints (replaces Download)

**`POST /api/sort/start`**
- Request: `{ "album_ids": string[] }`
- Response: `{ "total_files": number }`
- Moves files from iCloud Photos folder into album-named subfolders

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
```json
{
  "icloud_folder": "C:\\Users\\user\\Pictures\\iCloud Photos\\Photos",
  "license_key": "XXXX-XXXX-XXXX-XXXX"
}
```

**`PUT /api/settings`**
- Partial updates allowed
- Response: full settings after update

### License Endpoints (NEW)

**`POST /api/license/validate`**
- Request: `{ "key": string }`
- Response: `{ "valid": true, "expires_at": "2026-04-12" }` or `{ "valid": false, "error": "invalid_key" }`

**`GET /api/license/status`**
- Response: `{ "activated": boolean, "expires_at": string | null }`

### Standard Error Response

```json
{ "error": "<error_code>", "message": "<human-readable detail>" }
```

Error codes: `invalid_credentials`, `2fa_required`, `2fa_failed`, `session_expired`, `not_authenticated`, `sort_in_progress`, `file_not_found`, `permission_denied`, `invalid_license`, `license_expired`, `internal_error`

## 8. Frontend Screens

Four screens, linear flow:

### Screen 1: License Activation
- License key input + "Activate" button
- Link to purchase page
- Shown on first launch or if license expired

### Screen 2: Authentication
- Apple ID + password → 2FA code
- Reuse existing `AuthScreen.tsx`

### Screen 3: Album Picker
- List of albums with checkboxes, name, and file count
- No need to expand/show individual files (users with 100K+ images don't care)
- Select all / deselect all
- "Sort Selected" button
- Shows which albums were previously sorted (greyed out / checkmark)
- "Refresh from iCloud" button to re-fetch metadata

### Screen 4: Sort Progress
- Overall progress bar (X / Y files)
- Current file + current album
- Error list at bottom
- Completion summary when done

## 9. Project Structure

```
icloud-sorter/
├── frontend/                    # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── LicenseScreen.tsx
│   │   │   ├── AuthScreen.tsx
│   │   │   ├── AlbumPicker.tsx
│   │   │   └── SortProgress.tsx
│   │   ├── hooks/useApi.ts
│   │   ├── types/api.ts
│   │   └── styles/index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/                     # Python FastAPI
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth.py
│   │   ├── albums.py
│   │   ├── sort.py
│   │   ├── settings.py
│   │   └── license.py
│   ├── services/
│   │   ├── icloud_service.py    # auth + album/asset metadata
│   │   ├── sorter_service.py    # file move engine
│   │   └── state_service.py     # SQLite (one table)
│   └── models/
│       ├── schemas.py
│       └── db.py
│
├── website/                     # Landing page + purchase (Phase 2)
│
├── .github/workflows/
│   ├── build.yml
│   └── release.yml
│
├── PLANNING_SORTER.md
├── README.md
├── LICENSE
└── .gitignore
```

## 10. Implementation Phases

### Phase 1: Core Sorter Backend (Week 1)
1. Refactor SQLite schema (`db.py`) — new tables for sort operations
2. Build `metadata_service.py` — fetch + cache album/asset data from iCloud
3. Build `sorter_service.py`:
   - Scan source folder for files
   - Match local files to iCloud assets by filename
   - Create album folders with sanitized names
   - Copy/move files with collision resolution
   - Track operations in SQLite
   - SSE progress streaming
4. Wire up new routers: `sort.py`, `metadata.py`
5. Update `schemas.py` with new Pydantic models
6. Update `settings.py` for new settings fields
7. Remove `download.py` router and `download_service.py`

### Phase 2: Frontend Adaptation (Week 1-2)
1. Update `types/api.ts` for new API contract
2. Update `useApi.ts` with new endpoint functions
3. Add `SortConfig.tsx` — folder pickers, operation type
4. Add `SortPreview.tsx` — planned operations tree
5. Adapt `DownloadProgress.tsx` → `SortProgress.tsx`
6. Update `AlbumBrowser.tsx` — add metadata sync button
7. Update `Settings.tsx` for new fields
8. Update `App.tsx` — new screen flow

### Phase 3: Licensing (Week 2)
1. Choose provider (Keygen.sh / LemonSqueezy / Gumroad)
2. Build `license_service.py` — API-based key validation
3. Build `license.py` router
4. Build `LicenseScreen.tsx` frontend
5. Add license check to app startup flow

### Phase 4: Website (Week 2-3)
1. Landing page with product description
2. Purchase flow integration (provider's checkout)
3. Download link (post-purchase)
4. FAQ, prerequisites, support contact
5. Deploy to Vercel/Netlify

### Phase 5: Desktop Packaging (Week 3)
1. Electron wrapper (spawns Python backend as child process)
2. Or: PyInstaller single-exe (simpler, no auto-update)
3. Windows code signing certificate
4. Installer (NSIS or electron-builder)

### Phase 6: CI/CD (Week 3-4)
1. GitHub Actions: lint + test on PR
2. GitHub Actions: build `.exe` on tag
3. Code signing in CI
4. Auto-update mechanism (electron-updater or Sparkle-like)
5. Website auto-deploy on push to `main`

## 11. Key Design Decisions to Make

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | **Packaging** | Electron / Tauri / PyInstaller / None | PyInstaller for MVP, Electron for v2 |
| 2 | **License provider** | Keygen.sh / LemonSqueezy / Gumroad | LemonSqueezy (simple, handles EU VAT) |
| 3 | **Cross-album duplicates** | Move to first album / Move + leave shortcut | Move to first album, skip in subsequent |
| 4 | **Auto-detect iCloud folder** | Registry / Known paths / Manual | Try known paths, fall back to manual |

## 12. What to Delete from Current Codebase

- `backend/routers/download.py`
- `backend/services/download_service.py`
- `frontend/src/components/DownloadProgress.tsx`
- Download-related types/schemas
- `PLANNING.md` (Go/Wails plan — obsolete)
- `PLANNING_CLOUD.md` (cloud deployment — obsolete)
- `GUI_FRAMEWORK_COMPARISON.md` (decision made)

## 13. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Filename mismatch** between pyicloud and local files | Files can't be sorted | Case-insensitive match, fallback to size+name, report unmatched |
| **pyicloud auth breakage** (Apple changes endpoints) | App unusable until fix | Monitor pyicloud repo, have fallback messaging in UI |
| **Large libraries (50K+ photos)** | Slow metadata fetch | Cache aggressively in SQLite, show progress during sync |
| **iCloud for Windows changes sync folder structure** | Auto-detect breaks | Manual folder picker as fallback |
| **License system complexity** | Delays launch | Start with simple key validation, no DRM |
| **Windows-specific filesystem issues** | NTFS long paths, permissions | Use `\\?\` prefix for long paths, handle PermissionError gracefully |
| **Moving files breaks iCloud sync** | Data loss risk | Default to COPY, warn on MOVE with confirmation dialog |
