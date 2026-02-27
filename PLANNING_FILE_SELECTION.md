# File-Level Selection & Download — Feature Plan

*Extends PLANNING_MVP.md — adds per-file download selection to the existing album-based workflow.*

---

## Summary

The MVP only supports downloading entire albums. This feature adds the ability to select individual files within albums and download just those files. Downloaded files are placed into their album's folder, same as whole-album downloads.

---

## User Flow

1. User authenticates (unchanged)
2. User browses albums, expands an album to see its assets (existing UI)
3. **New:** User selects individual files via checkboxes in the asset table
4. **New:** User can mix selections — some whole albums, some individual files from other albums
5. User clicks "Download Selected" — downloads only the selected items
6. Files land in `<download_path>/<album_folder_name>/` as before

---

## API Changes

### Modified Endpoint: `POST /api/download/start`

The request body gains an optional `asset_selections` field:

**Request (album-only, unchanged):**
```json
{
  "album_ids": ["album-1", "album-2"],
  "download_path": "/home/user/photos"
}
```

**Request (file-level selection):**
```json
{
  "album_ids": ["album-1"],
  "asset_selections": {
    "album-2": ["asset-id-1", "asset-id-2", "asset-id-5"]
  },
  "download_path": "/home/user/photos"
}
```

**Behavior:**
- `album_ids`: Download ALL assets from these albums (existing behavior)
- `asset_selections`: Download ONLY the listed assets, keyed by album ID. Each asset is placed in that album's folder
- Both fields can be used together in a single request (e.g., download all of album-1, but only 3 files from album-2)
- If both fields are empty, return `not_found` error

**Response:** Unchanged — `{ "job_id", "total_assets", "estimated_bytes" }`

### All Other Endpoints: Unchanged

Album listing, asset listing, progress SSE, pause, cancel, settings — no changes.

---

## Backend Changes

### `backend/models/schemas.py`

Add optional `asset_selections` to `DownloadStartRequest`:

```python
class DownloadStartRequest(BaseModel):
    album_ids: list[str] = []                              # whole albums (was required, now defaults to [])
    asset_selections: dict[str, list[str]] | None = None   # album_id -> [asset_id, ...]
    download_path: str
```

### `backend/services/download_service.py`

Modify `start()` to handle `asset_selections`:

- When `asset_selections` is provided, for each `album_id -> asset_ids` entry:
  - Fetch all assets from that album (existing `get_album_assets` call)
  - Filter to only the requested `asset_ids`
  - Create download records only for the filtered assets
- `album_ids` continues to work as before (download all assets)
- The two modes combine: assets from `album_ids` (all) + assets from `asset_selections` (filtered)

### `backend/routers/download.py`

Pass `asset_selections` from the request to `download_service.start()`.

### No Database Schema Changes

The existing `downloads` table already tracks per-asset records with `(asset_id, album_id, version)`. File-level selection just means fewer records are created — the schema handles it as-is.

---

## Frontend Changes

### `frontend/src/types/api.ts`

Update `DownloadStartRequest`:

```typescript
export interface DownloadStartRequest {
  album_ids: string[];
  asset_selections?: Record<string, string[]>;  // album_id -> asset_ids
  download_path: string;
}
```

### `frontend/src/components/AlbumBrowser.tsx`

The main UI change:

- **Add checkboxes to each row in the asset table** (when album is expanded)
- **Add "Select All" / "Deselect All" per album** for assets within an expanded album
- **Track selected assets** in state: `Map<string, Set<string>>` (album_id → selected asset_ids)
- **Update "Download Selected" button** to include both whole-album selections AND per-file selections
- **Show selection count** that reflects total: whole-album asset counts + individually selected file counts

**Selection logic:**
- If an album checkbox is checked, the entire album is selected (existing behavior, goes into `album_ids`)
- If individual files are checked within an album (but not the album checkbox), only those files are selected (goes into `asset_selections`)
- If a user checks the album checkbox after selecting some files, it promotes to whole-album selection
- If a user unchecks the album checkbox, it clears both the album selection and any file selections within it

### `frontend/src/hooks/useApi.ts`

Update `startDownload` to accept and pass `asset_selections`:

```typescript
export async function startDownload(
  albumIds: string[],
  downloadPath: string,
  assetSelections?: Record<string, string[]>,
): Promise<DownloadStartResponse> {
  return apiFetch<DownloadStartResponse>('/api/download/start', {
    method: 'POST',
    body: JSON.stringify({
      album_ids: albumIds,
      download_path: downloadPath,
      ...(assetSelections && { asset_selections: assetSelections }),
    }),
  });
}
```

### `frontend/src/App.tsx`

Update `handleStartDownload` and `downloadState` to carry `assetSelections`:

```typescript
const [downloadState, setDownloadState] = useState<{
  albumIds: string[];
  assetSelections?: Record<string, string[]>;
  downloadPath: string;
} | null>(null);
```

### `frontend/src/components/DownloadProgress.tsx`

Pass `assetSelections` to `startDownload` call. No other changes — progress tracking is already per-asset.

---

## What Does NOT Change

- **Download pipeline** — atomic writes, temp files, filename collision resolution, cross-album copy optimization — all unchanged
- **SSE progress streaming** — already per-asset, works identically
- **Pause / Cancel** — unchanged
- **Disk space checking** — unchanged (sums only selected assets)
- **Settings** — unchanged
- **Database schema** — unchanged
- **Album listing / asset listing endpoints** — unchanged
- **Auth flow** — unchanged

---

## Implementation Checklist

- [ ] Update `DownloadStartRequest` in `schemas.py` — add optional `asset_selections`
- [ ] Update `download_service.start()` — handle filtered asset downloads
- [ ] Update `download.py` router — pass `asset_selections`
- [ ] Update `DownloadStartRequest` in `types/api.ts` — add optional `asset_selections`
- [ ] Update `startDownload` in `useApi.ts` — accept and pass `asset_selections`
- [ ] Add per-file checkboxes to `AlbumBrowser.tsx` asset table
- [ ] Add asset selection state management to `AlbumBrowser.tsx`
- [ ] Update `AlbumBrowser.onStartDownload` prop to include asset selections
- [ ] Update `App.tsx` — carry `assetSelections` through download flow
- [ ] Update `DownloadProgress.tsx` — pass `assetSelections` to `startDownload`
- [ ] Verify: selecting whole album still works as before
- [ ] Verify: selecting individual files downloads only those files into correct album folders
- [ ] Verify: mixed selection (whole albums + individual files) works in a single download job
