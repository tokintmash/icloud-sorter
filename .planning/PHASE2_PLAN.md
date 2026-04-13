# Phase 2: Frontend — Implementation Plan

**Source of truth:** `.planning/PLANNING_SORTER_v2.md` §10 Phase 2  
**Scope:** Rewrite the download-oriented frontend to match the Phase 1 sorter backend.

## Status: 🔲 NOT STARTED

---

## Current State

The frontend is a **photo downloader UI**: `AlbumBrowser.tsx` has expandable asset lists with per-file details (size, dimensions, type), `DownloadProgress.tsx` tracks byte-level download progress with pause/resume/cancel, `Settings.tsx` has four download-related fields, and `types/api.ts` still contains all old download types (`AssetInfo`, `DownloadProgressEvent`, `PauseResponse`, etc.).

## Target State

A **photo sorter UI**: `AlbumPicker.tsx` shows albums with checkboxes and file counts (no per-file expansion), `SortProgress.tsx` streams SSE file-count progress, `Settings.tsx` has only `icloud_folder`, and `types/api.ts` matches `backend/models/schemas.py` exactly.

---

## Work Items

| ID | Work Item | Files | Depends On |
|----|-----------|-------|------------|
| W1 | Types + API hooks | `types/api.ts`, `hooks/useApi.ts` | — |
| W2 | AlbumPicker component | `components/AlbumPicker.tsx` (new), delete `AlbumBrowser.tsx` | W1 |
| W3 | SortProgress component | `components/SortProgress.tsx` (new), delete `DownloadProgress.tsx` | W1 |
| W4 | Settings rewrite | `components/Settings.tsx` | W1 |
| W5 | App shell + CSS cleanup | `App.tsx`, `styles/index.css` | W2, W3, W4 |

### Dependency Graph

```
W1 ──→ W2 ──→ W5
  ├──→ W3 ──┘
  └──→ W4 ──┘
```

**Parallel batches:**
1. **Batch 1:** W1 (types + hooks — everything depends on this)
2. **Batch 2:** W2 + W3 + W4 (independent components, all depend only on W1)
3. **Batch 3:** W5 (app shell wiring + CSS cleanup, after all components exist)

---

## Detailed Specifications

### W1 — Types + API Hooks

#### `frontend/src/types/api.ts`

**Keep unchanged:** `ErrorResponse`, `LoginRequest`, `LoginResponse`, `TwoFactorRequest`, `TwoFactorResponse`, `SessionResponse`, `AlbumInfo`, `AlbumListResponse`.

**Remove:** `AssetInfo`, `AssetListResponse`, `DownloadStartRequest`, `DownloadStartResponse`, `DownloadError`, `DownloadProgressEvent`, `PauseResponse`, `CancelResponse`, old `SettingsResponse`, old `SettingsUpdateRequest`.

**Add** (must match `backend/models/schemas.py` exactly):
```typescript
// Sort types
export interface SortStartRequest {
  album_ids: string[];
}

export interface SortStartResponse {
  total_files: number;
}

export interface SortError {
  filename: string;
  error: string;
  album: string;
}

export interface SortProgressEvent {
  status: 'sorting' | 'complete' | 'error';
  total_files: number;
  completed_files: number;
  failed_files: number;
  current_file: string;
  current_album: string;
  errors: SortError[];
}

// Settings types
export interface SettingsResponse {
  icloud_folder: string;
}

export interface SettingsUpdateRequest {
  icloud_folder?: string;
}
```

#### `frontend/src/hooks/useApi.ts`

**Keep unchanged:** `ApiError`, `apiFetch`, `login`, `submit2fa`, `getSession`, `getAlbums`, `getSettings`, `updateSettings`.

**Remove:** `getAlbumAssets`, `startDownload`, `pauseDownload`, `resumeDownload`, `cancelDownload`.

**Remove from imports:** `AssetListResponse`, `DownloadStartResponse`, `PauseResponse`, `CancelResponse`.

**Update `SettingsUpdateRequest` import** — same name, new shape (already compatible since it uses `apiFetch`).

**Add:**
```typescript
export async function startSort(albumIds: string[]): Promise<SortStartResponse> {
  return apiFetch<SortStartResponse>('/api/sort/start', {
    method: 'POST',
    body: JSON.stringify({ album_ids: albumIds }),
  });
}
```

Note: SSE for `/api/sort/progress` is handled directly in `SortProgress.tsx` via `EventSource` — no hook needed.

---

### W2 — AlbumPicker Component

**Create `frontend/src/components/AlbumPicker.tsx`**, then **delete `AlbumBrowser.tsx`**.

This replaces the old album browser. Key differences from `AlbumBrowser.tsx`:
- **No expandable asset list** — no per-file details (users with 100K+ photos don't need it)
- **No `getAlbumAssets()` calls** — that endpoint no longer exists
- Button says "Sort Selected" not "Download Selected"
- Shows `folder_name` per album (from `AlbumInfo`)

**Props:**
```typescript
interface AlbumPickerProps {
  onSessionExpired: () => void;
  onStartSort: (albumIds: string[]) => void;
}
```

**Behavior:**
1. On mount, call `getAlbums()` — show spinner while loading
2. Display album list: checkbox, album name, file count (`{asset_count} files`), folder name (muted)
3. Select All / Deselect All buttons
4. "Sort Selected (N)" primary button — calls `onStartSort(selectedAlbumIds)`
5. "Refresh from iCloud" button — re-calls `getAlbums()`
6. Handle `session_expired` / `not_authenticated` errors → `onSessionExpired()`

**Layout:** Flat list of cards (no chevron/expand). Each album row:
```
[✓] Vacation 2024        1,234 files    → Vacation 2024/
```

Reuse existing CSS classes: `.album-browser` → rename to `.album-picker`, `.album-toolbar`, `.album-list`, `.album-card`, `.album-header`, `.album-select-checkbox`, `.album-info`, `.album-name`, `.album-count`.

---

### W3 — SortProgress Component

**Create `frontend/src/components/SortProgress.tsx`**, then **delete `DownloadProgress.tsx`**.

Key differences from `DownloadProgress.tsx`:
- **No byte-level tracking** — progress is file count only
- **No pause/resume/cancel** — file moves are instant, no need
- **No download path** — sorter uses configured `icloud_folder`
- SSE endpoint is `/api/sort/progress` not `/api/download/progress`
- Simpler status: `sorting` | `complete` | `error` (no `paused`/`cancelled`)

**Props:**
```typescript
interface SortProgressProps {
  albumIds: string[];
  onComplete: () => void;
  onSessionExpired: () => void;
}
```

**Behavior:**
1. On mount, call `startSort(albumIds)` → get `total_files`
2. Open `EventSource('/api/sort/progress')`
3. Parse each SSE message as `SortProgressEvent`
4. Display:
   - Status label: "Sorting..." / "Complete" / "Error"
   - Progress bar: `completed_files / total_files` percentage
   - Current file + current album (muted text below bar)
   - Stats: `"{completed} / {total} files"` and `"{failed} failed"` if any
   - Error list at bottom (collapsible if >5)
5. On terminal status (`complete` | `error`): close EventSource, show summary + "Done" button
6. "Done" button calls `onComplete()`
7. Handle SSE errors gracefully (EventSource auto-reconnects)

**Layout:** Reuse existing CSS: `.download-progress` → keep or rename to `.sort-progress`, `.progress-bar-container`, `.progress-bar-fill`, `.progress-stats`, `.download-summary` → `.sort-summary`, `.download-errors` → `.sort-errors`, `.error-list`.

---

### W4 — Settings Rewrite

**Rewrite `frontend/src/components/Settings.tsx`** in place.

**Remove:** `downloadPath`, `concurrentDownloads`, `metadataDelayMs`, `maxRetries` state + form fields.

**Keep:** Loading state, save flow, error/success messages, form structure.

**Single field:** `icloud_folder` (string input).

```typescript
const [icloudFolder, setIcloudFolder] = useState('');
```

**Form:**
```
iCloud Photos Folder
[___C:\Users\...\iCloud Photos\Photos___]

[Save Settings]
```

**Behavior:** Same as current — load on mount, save on submit, show success/error. The `getSettings()` and `updateSettings()` hooks already return/accept the new shape after W1.

---

### W5 — App Shell + CSS Cleanup

#### `frontend/src/App.tsx`

**Changes:**
1. Title: `"iCloud Photo Downloader"` → `"iCloud Photo Sorter"`
2. Import `AlbumPicker` instead of `AlbumBrowser`, `SortProgress` instead of `DownloadProgress`
3. Replace `Tab = 'albums' | 'downloads' | 'settings'` → `Tab = 'albums' | 'sorting' | 'settings'`
4. Replace `downloadState` with `sortState: { albumIds: string[] } | null`
5. Replace `handleStartDownload` with `handleStartSort`:
   - Just set `sortState` and switch to sorting tab (no need to fetch settings for download_path)
6. Replace `handleDownloadComplete` with `handleSortComplete`:
   - Clear `sortState`, switch back to albums tab
7. Nav: "Downloads" → "Sorting" (or remove tab, show inline)
8. Render `AlbumPicker` with `onStartSort`, `SortProgress` with sort props

**Screen flow (linear, not tabs):**
- Unauthenticated → AuthScreen
- Authenticated + no sort active → AlbumPicker (with Settings accessible via nav)
- Sort active → SortProgress

**Alternative (simpler, recommended):** Keep tab navigation but rename:
- "Albums" tab → shows `AlbumPicker`
- "Sorting" tab → shows `SortProgress` (or "select albums first" message)
- "Settings" tab → shows `Settings`

#### `frontend/src/styles/index.css`

**Minimal changes:**
1. Rename `.album-browser` → `.album-picker` (if CSS class changes)
2. Remove `.asset-list` styles (table, th, td, `.load-more`) — no longer needed
3. Rename `.download-progress` → `.sort-progress` (optional, can keep)
4. Remove `.download-actions` styles (no pause/resume/cancel buttons)
5. Remove `.progress-bar-fill.paused` (no paused state)
6. Keep all other styles — they work as-is

---

## Subagent Strategy

### Subagent A — Types + API Hooks (W1)
**Files:** `frontend/src/types/api.ts`, `frontend/src/hooks/useApi.ts`

### Subagent B — AlbumPicker (W2)
**Files:** Create `frontend/src/components/AlbumPicker.tsx`, delete `frontend/src/components/AlbumBrowser.tsx`

### Subagent C — SortProgress (W3)
**Files:** Create `frontend/src/components/SortProgress.tsx`, delete `frontend/src/components/DownloadProgress.tsx`

### Subagent D — Settings (W4)
**Files:** `frontend/src/components/Settings.tsx`

*Subagents B, C, D run in parallel after A completes.*

### Subagent E — App Shell + CSS (W5)
**Files:** `frontend/src/App.tsx`, `frontend/src/styles/index.css`

*Runs last, after B, C, D complete.*

---

## Verification

1. `cd frontend && npm run build` — zero TS errors, zero warnings
2. `npm run dev` — app loads at `http://localhost:5173`
3. Auth flow works: login → 2FA → authenticated
4. Album list loads with checkboxes + counts
5. "Sort Selected" triggers sort → progress screen with SSE
6. Settings shows only `icloud_folder`, round-trips correctly
7. No references to `download`, `DownloadProgress`, `AlbumBrowser`, `AssetInfo`, `asset_id`, or old settings fields remain in frontend code
