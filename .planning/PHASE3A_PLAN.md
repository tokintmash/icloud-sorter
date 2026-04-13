# Phase 3A: Cross-Album Duplicate Handling — Implementation Plan

**Status:** Not started  
**Dependencies:** None (standalone)

---

## Context

When a photo belongs to multiple iCloud albums, the sorter must decide what to do during the move. Currently the sorter always uses "move to first album, skip in subsequent" (hardcoded in `sorter_service.py` via the `claimed` set).

This phase adds a user-facing setting with two options, plus leaves room for a third option later.

---

## Options to Implement Now

### Option 1: Move to First Album Only (current default)

- File is moved to the first album folder encountered
- Subsequent albums referencing the same file are marked `failed` with error `"Already moved to another album"`
- **No sort logic changes needed** — this is the existing behavior
- Only change: make it a named, selectable setting rather than implicit behavior

### Option 2: Copy to Each Album

- File is copied (`shutil.copy2`) into every album folder it belongs to
- Each album folder is fully self-contained — useful for the workflow: organize → copy folders to external storage → delete from iCloud
- **Warning:** temporarily increases disk usage (a file in 3 albums = 3 copies on disk)
- Implementation: don't use the `claimed` set; use `shutil.copy2` instead of `os.rename` for the 2nd+ album, or copy to all and remove the original

### Potential Future Option 3: Move + Cross-Reference Report (DEFERRED)

- Same move behavior as Option 1 (file moves once)
- Additionally generates a `_cross_album_report.csv` in the iCloud folder root listing every file and all albums it belongs to
- Zero extra disk usage; user gets a reference for which other albums each file belonged to
- **NOT implemented in this phase** — may be added later
- See "Future Option 3" section at end of this file

---

## Setting Value

A single string setting `duplicate_handling` with values:
- `"move_only"` — Option 1 (default)
- `"copy_to_each"` — Option 2
- (Future: `"move_with_report"` — Option 3)

Default: `"move_only"` (preserves current behavior)

---

## Files to Change

### 1. Backend: `backend/config.py`

- Add `"duplicate_handling"` to `_get_defaults()` with default value `"move_only"`
- No other changes — `load_settings()` / `save_settings()` already handle arbitrary keys

### 2. Backend: `backend/models/schemas.py`

- Add `duplicate_handling: str` to `SettingsResponse`
- Add `duplicate_handling: Optional[str] = None` to `SettingsUpdateRequest`

### 3. Backend: `backend/services/sorter_service.py`

**Main changes in `_run_sort()`:**

1. `start()`: read `duplicate_handling` from settings, pass to `_run_sort()`
2. `_run_sort()` accepts `duplicate_handling` parameter

**When `duplicate_handling == "move_only"` (default):** no changes — existing behavior with `claimed` set.

**When `duplicate_handling == "copy_to_each"`:**

- Don't skip files via the `claimed` set — every album gets the file
- First occurrence: `os.rename()` (move, instant on same drive)
- Subsequent occurrences: `shutil.copy2()` from wherever the file now is (use updated `file_index`)
- All occurrences marked as `sorted` (no failures for cross-album files)

**Detailed logic change (~lines 113-134):**

```python
# Current code (move_only — keep as-is for that mode):
unclaimed = [c for c in candidates if c not in claimed]
if not unclaimed:
    state_service.mark_album_file_failed(album_id, filename, "Already moved to another album")
    ...
    continue
source = unclaimed[0]
claimed.add(source)
os.rename(str(source), str(target_path))

# New code for copy_to_each mode:
# Pick any candidate (no claimed filtering)
source = candidates[0]
if source.parent == target_dir:
    # Already in target — nothing to do
    state_service.mark_album_file_sorted(album_id, filename)
    self._completed_files += 1
    continue
target_path = target_dir / source.name
# ... collision handling (same as existing) ...
if source not in claimed:
    # First time seeing this file — move it
    os.rename(str(source), str(target_path))
    claimed.add(source)
    # Update file_index
else:
    # File already moved to another album — copy from there
    shutil.copy2(str(source), str(target_path))
```

### 4. Backend: `backend/routers/settings.py`

- No changes needed — already handles arbitrary fields via `request.model_dump(exclude_none=True)`

### 5. Frontend: `frontend/src/types/api.ts`

- Add `duplicate_handling: string` to `SettingsResponse`
- Add `duplicate_handling?: string` to `SettingsUpdateRequest`

### 6. Frontend: `frontend/src/components/Settings.tsx`

- Add radio button group for "Cross-Album Duplicates":
  - `"move_only"`: **Move to first album only** — subtitle: "Each file is placed in one album folder. If a file belongs to multiple albums, it goes to the first one processed."
  - `"copy_to_each"`: **Copy to each album** — subtitle: "Each file is copied into every album folder it belongs to. Uses more disk space."
- Load and save the `duplicate_handling` value alongside `icloud_folder`
- Show a small warning/note when `"copy_to_each"` is selected about increased disk usage
- Style: match existing form layout (label + inputs inside `.form-group`)

### 7. Frontend: `frontend/src/components/SortProgress.tsx`

- No changes needed for these two options
- When `move_only`: failed files still show "Already moved to another album" in error list (existing behavior)
- When `copy_to_each`: no cross-album failures occur, so no special UI needed

---

## Implementation Order

1. **Backend settings** — `config.py` defaults + `schemas.py` fields (5 min)
2. **Frontend types** — `api.ts` type updates (2 min)
3. **Frontend Settings UI** — radio buttons in `Settings.tsx` (15 min)
4. **Backend sorter logic** — copy mode in `sorter_service.py` (20 min)
5. **Test** — end-to-end with files that belong to multiple albums (10 min)

**Estimated total: ~50 minutes**

---

## Acceptance Criteria

- [ ] Settings UI shows two radio options for duplicate handling
- [ ] Default is "Move to first album only" (matches current behavior exactly)
- [ ] "Copy to each album" mode: files are copied (`shutil.copy2`) into every album folder
- [ ] "Copy to each album" mode: no files are marked as failed due to cross-album duplicates
- [ ] "Copy to each album" mode: disk space warning shown in Settings UI
- [ ] Setting persists across app restarts
- [ ] Frontend builds with zero TS errors

---

## Future Option 3: Move + Cross-Reference Report

**Deferred — tracked in `PHASE3_BREAKDOWN.md` and `PLANNING_SORTER_v2.md`.**

When the time comes, implementation is minimal since the setting infrastructure is already in place:

1. Add `"move_with_report"` value to the setting + a third radio button
2. In `sorter_service.py`, when `duplicate_handling == "move_with_report"`:
   - Same move logic as `"move_only"`
   - But mark cross-album skips as `sorted` instead of `failed`
   - After sort loop, generate `_cross_album_report.csv` in iCloud folder root
   - Columns: `filename`, `moved_to_album`, `also_in_albums`
   - Only include files that appear in 2+ selected albums
3. Add report path to sort completion progress so the UI can mention it
4. ~20 minutes of work, no schema or API changes needed (setting field already exists)
