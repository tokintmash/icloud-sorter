# Phase 3B Code Review Findings

Reviewed: 2026-04-14

## Critical

### 1. Directory traversal in SPA fallback
**File:** `backend/app.py` L67–70  
**Severity:** Critical  

The SPA fallback handler builds a file path via `FRONTEND_DIST / full_path` without validating that the resolved path stays within `FRONTEND_DIST`. A request with `..` segments (e.g., `GET /../../Windows/win.ini`) can read arbitrary files on the filesystem.

**Fix:** Resolve the path and verify it is relative to `FRONTEND_DIST` before serving:
```python
file_path = (FRONTEND_DIST / full_path).resolve()
if file_path.is_relative_to(FRONTEND_DIST.resolve()) and file_path.is_file():
    return FileResponse(str(file_path))
```

---

## High

### 2. `/api/app/quit` doesn't close the pywebview window
**File:** `desktop_launcher.py` L89–96  
**Severity:** High  

The `/api/app/quit` endpoint sets `server.should_exit = True` via the lifecycle callback, but the pywebview window has no corresponding close trigger. The backend exits while the native window hangs open indefinitely.

**Fix:** After creating the window but before `webview.start()`, register a shutdown callback that destroys it:
```python
from backend.lifecycle import register_shutdown_callback
register_shutdown_callback(lambda: window.destroy())
```
This should be registered **in addition to** the existing server shutdown callback.

---

## Medium

### 3. Fragile `hiddenimports` list in PyInstaller spec
**File:** `icloud_sorter.spec` L17–50  
**Severity:** Medium  

The spec explicitly lists every `backend.*` submodule and many `uvicorn.*` internals. This is brittle — any new module requires a spec update, and PyInstaller already discovers most of these automatically via static analysis. There are no built-in PyInstaller hooks for uvicorn, so the uvicorn entries are justified, but the `backend.*` entries are unnecessary since `desktop_launcher.py` imports `backend.app` at the top level and PyInstaller follows the import chain.

**Fix:** Remove all `backend.*` entries from `hiddenimports` and keep only the uvicorn internals, `pyicloud`, `webview`, and `certifi`.

---

## Low

### 4. `onedir` + `console=False` mismatch with plan
**File:** `icloud_sorter.spec` L63–86  
**Severity:** Low  

The spec is configured as a directory build (`COLLECT` block, `exclude_binaries=True`) but sets `console=False`. The Phase 3B plan says to start with `onedir` + `console=True` for debugging, then switch to `onefile` + `console=False` for release. Currently it mixes the debug layout with the release console setting, which hides error output during the debugging phase.

**Fix:** For debugging: set `console=True`. For release: remove the `COLLECT` block, set `exclude_binaries=False`, and move `a.binaries`, `a.zipfiles`, `a.datas` into the `EXE` definition for a single-file build.

### 5. Registry key may not match iCloud Photos
**File:** `backend/config.py` L26–29  
**Severity:** Low  

The registry lookup checks `Software\Apple Inc.\iCloud\iCloudDriveDesktop` with a `PhotosPath` value. This key is primarily for iCloud Drive. iCloud Photos paths are sometimes found under `Software\Apple Inc.\Internet Services`. The current code is best-effort and fails gracefully, so this is not a bug — but adding the alternative key as a fallback would improve detection reliability.

---

## Runtime

### 6. Missing `fido2` data file in PyInstaller bundle
**File:** `icloud_sorter.spec` L13–16  
**Severity:** High  

The `fido2` library (transitive dependency via `pyicloud`) requires `public_suffix_list.dat` at runtime. PyInstaller does not bundle it automatically, causing a `FileNotFoundError` when the `.exe` is launched.

**Fix:** Add the `fido2` data file to the `datas` list in `icloud_sorter.spec`:
```python
import fido2, os
fido2_dir = os.path.dirname(fido2.__file__)
```
Then in `datas`:
```python
(os.path.join(fido2_dir, 'public_suffix_list.dat'), 'fido2'),
```

### 7. Build script em-dash encoding issue (FIXED)
**File:** `scripts/build_windows.ps1`  
**Severity:** High  

UTF-8 em-dashes (`—`) in the script caused silent failures on Windows PowerShell 5.1, which reads scripts as ANSI without a BOM. The script would stop executing after Step 1 without any error message.

**Status:** Fixed — replaced all em-dashes with ASCII dashes.

### 8. `pythonnet` incompatible with Python 3.14 (FIXED)
**File:** `requirements-build.txt`  
**Severity:** High  

The stable `pythonnet` release (3.0.5) does not support Python 3.14. `pywebview` depends on `pythonnet` on Windows, causing `pip install` to fail.

**Status:** Fixed — pinned `pythonnet>=3.1.0rc0` in `requirements-build.txt` and added `--pre` to the pip install command in the build script.

---

## Positive Notes

- `runtime_paths.py` and `lifecycle.py` are clean, minimal, and correct.
- `config.py` registry detection has proper `sys.platform` guards and exception handling (`OSError`, `ImportError`, `FileNotFoundError`).
- `dev_server.py` correctly uses the import string (`"backend.app:app"`) with `reload=True` for dev, while `desktop_launcher.py` correctly uses the app object directly with `reload=False` for production.
- Build script (`build_windows.ps1`) validates the frontend build output before proceeding.
- `requirements-build.txt` correctly references `-r backend/requirements.txt` to include runtime deps.
