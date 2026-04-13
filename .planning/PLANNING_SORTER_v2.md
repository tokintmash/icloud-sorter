# PLANNING: iCloud Photo Sorter — MVP v2

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

## 3. Tech Stack (MVP)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React + TypeScript + Vite | Already built, reuse existing code. |
| **Backend** | Python (FastAPI + uvicorn) | Keeps pyicloud in-process. |
| **iCloud API** | `pyicloud` (timlaing fork) | Only maintained library for iCloud auth + Photos API. |
| **State DB** | SQLite (`sqlite3` stdlib) | One table for album/file metadata + sort status. |
| **CI/CD** | GitHub Actions | Build + test. |

### Post-MVP considerations
- **Desktop packaging:** Electron or PyInstaller for `.exe` distribution
- **Licensing:** Keygen.sh / LemonSqueezy / Gumroad
- **Website:** Landing page + purchase flow
- **Auto-update:** electron-updater or custom
- **Code signing:** Windows certificate for installer

## 4. Core Data Flow

```
1. User launches app
2. User authenticates with Apple ID (pyicloud: SRP + 2FA)
3. App fetches album list (names + counts) from iCloud API — fast, no asset iteration
4. User sees album list with file counts, picks albums to sort
5. On sort start: app fetches per-file metadata for selected albums only, stores in SQLite
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
| File exists locally but not in any album | Leave in place (ignored) |
| Live Photos (IMG_1234.HEIC + IMG_1234.MOV) | Match both files, keep together in album folder |
| Edited photos | iCloud for Windows syncs originals; match by original filename |
| RAW+JPEG pairs | Match both files (same base name, different extension) |
| Filename modified locally by user | Cannot match — report as unmatched |

### iCloud for Windows Folder Discovery
- Default path: `C:\Users\<username>\Pictures\iCloud Photos\Photos\`
- Alternative: `C:\Users\<username>\iCloudPhotos\`
- Registry key: `HKCU\Software\Apple Inc.\iCloud\` may contain the path
- Fallback: user manually selects folder in Settings

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
  "icloud_folder": "C:\\Users\\user\\Pictures\\iCloud Photos\\Photos"
}
```

**`PUT /api/settings`**
- Partial updates allowed
- Response: full settings after update

### Standard Error Response

```json
{ "error": "<error_code>", "message": "<human-readable detail>" }
```

Error codes: `invalid_credentials`, `2fa_required`, `2fa_failed`, `session_expired`, `not_authenticated`, `sort_in_progress`, `file_not_found`, `permission_denied`, `internal_error`

## 8. Frontend Screens

Four screens, linear flow + settings accessible from any screen:

### Screen 1: Authentication
- Apple ID + password → 2FA code
- Reuse existing `AuthScreen.tsx`

### Screen 2: Album Picker (main screen)
- List of albums with checkboxes, name, and file count
- No need to expand/show individual files (users with 100K+ images don't care)
- Select all / deselect all
- "Sort Selected" button
- Shows which albums were previously sorted (greyed out / checkmark)
- "Refresh from iCloud" button to re-fetch metadata

### Screen 3: Sort Progress
- Overall progress bar (X / Y files)
- Current file + current album
- Error list at bottom
- Completion summary when done

### Screen 4: Settings (accessible via gear icon / tab)
- **iCloud Photos folder path** — auto-detected on first launch, editable
- **Cross-album duplicates** *(post-MVP, shown disabled/greyed out)*:
  - "Copy to each album folder" — file appears in every album it belongs to (uses more disk space)
  - "Move to first album only" — file is moved once, skipped for subsequent albums
- About / version info

## 9. Project Structure

```
icloud-sorter/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── AuthScreen.tsx
│   │   │   ├── AlbumPicker.tsx
│   │   │   ├── SortProgress.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/useApi.ts
│   │   ├── types/api.ts
│   │   └── styles/index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth.py
│   │   ├── albums.py
│   │   ├── sort.py
│   │   └── settings.py
│   ├── services/
│   │   ├── icloud_service.py    # auth + album/asset metadata
│   │   ├── sorter_service.py    # file move engine
│   │   └── state_service.py     # SQLite (one table)
│   └── models/
│       ├── schemas.py
│       └── db.py
│
├── .github/workflows/
│   └── build.yml
│
├── PLANNING_SORTER_v2.md
├── README.md
├── LICENSE
└── .gitignore
```

## 10. Implementation Phases

### Phase 1: Core Sorter Backend
1. New SQLite schema (`db.py`) — single `album_files` table
2. Update `icloud_service.py` — fetch album list + filenames, populate SQLite
3. Build `sorter_service.py`:
   - Match filenames to local files (case-insensitive)
   - Create album folders with sanitized names
   - Move files into album folders
   - Track status in SQLite
   - SSE progress streaming
4. Build `sort.py` router
5. Update `settings.py` router for new settings (icloud_folder)
6. Update `schemas.py` with new Pydantic models
7. Remove `download.py` router and `download_service.py`

### Phase 2: Frontend
1. Update `types/api.ts` for new API contract
2. Update `useApi.ts` with new endpoint functions
3. Simplify `AlbumBrowser.tsx` → `AlbumPicker.tsx` (checkboxes + counts, no file expansion)
4. Adapt `DownloadProgress.tsx` → `SortProgress.tsx`
5. Add `Settings.tsx` — iCloud folder path config
6. Update `App.tsx` — new screen flow (Auth → Albums → Progress, Settings via tab/icon)

### Phase 3: Polish & Package (post-MVP)
1. Licensing integration
2. Cross-album duplicate handling option in Settings
3. Website + purchase flow
4. Desktop packaging (Electron or PyInstaller)
5. CI/CD for releases
6. Code signing

## 11. Key Design Decisions

| # | Decision | MVP Choice | Post-MVP Option |
|---|----------|------------|-----------------|
| 1 | **File operation** | Move (instant, same drive) | Add copy option |
| 2 | **Cross-album duplicates** | Move to first album, skip in subsequent | Phase 3A: add "copy to each album" option. Deferred: "move + CSV report" (see `PHASE3A_PLAN.md` → Future Option 3) |
| 3 | **iCloud folder detection** | Try known paths, fall back to manual in Settings | Registry lookup |
| 4 | **Licensing** | None (open/free) | LemonSqueezy or similar |
| 5 | **Packaging** | Run from source (python + npm) | PyInstaller `.exe` or Electron |

## 12. What to Delete from Current Codebase

- `backend/routers/download.py`
- `backend/services/download_service.py`
- `frontend/src/components/DownloadProgress.tsx`
- Download-related types/schemas in `schemas.py` and `types/api.ts`

## 13. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Filename mismatch** between pyicloud and local files | Files can't be sorted | Case-insensitive match, fallback to size+name, report unmatched |
| **pyicloud auth breakage** (Apple changes endpoints) | App unusable until fix | Monitor pyicloud repo, have fallback messaging in UI |
| **Large libraries (50K+ photos)** | Slow metadata fetch for selected albums at sort start | Only sync selected albums, cache in SQLite |
| **iCloud for Windows changes sync folder structure** | Auto-detect breaks | Manual folder picker in Settings as fallback |
| **Windows-specific filesystem issues** | NTFS long paths, permissions | Use `\\?\` prefix for long paths, handle PermissionError gracefully |
| **Moving files breaks iCloud sync** | Data loss risk | Test thoroughly; moving within iCloud folder preserves sync per user's confirmation |
