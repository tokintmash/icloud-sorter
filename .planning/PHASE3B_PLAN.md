# Phase 3B: Desktop Packaging — Implementation Plan

## Decision: PyInstaller (not Electron)

The app already serves the React frontend from FastAPI. Electron would add a second runtime, IPC complexity, and ~100MB+ bundle size for zero benefit. PyInstaller bundles everything into a single `.exe` that opens the user's browser.

## Architecture

```
User double-clicks iCloudPhotoSorter.exe
  → desktop_launcher.py (PyInstaller entry point)
    → Checks if already running on 127.0.0.1:8000
      → If yes: open browser, exit
      → If no:
        → Start uvicorn server (background thread, reload=False)
        → Poll /api/app/health every 250ms
        → When ready: open browser
        → Keep alive until server exits
    → "Exit App" button in UI → POST /api/app/quit → server.should_exit = True
```

## Tasks (in dependency order)

### 3B.1: `backend/runtime_paths.py` (no deps)
PyInstaller-safe path resolution. `bundle_root()` returns `sys._MEIPASS` when frozen, project root in dev. `frontend_dist()` returns the frontend build directory.

### 3B.2: `backend/lifecycle.py` (no deps)
Shutdown callback system. `register_shutdown_callback()` / `can_shutdown()` / `request_shutdown()`. Desktop launcher registers a callback; dev mode has none registered.

### 3B.3: Update `backend/app.py` (depends on 3B.1, 3B.2)
- Use `runtime_paths.frontend_dist()` for static files
- Add `GET /api/app/health` → `{"ok": true}`
- Add `POST /api/app/quit` → graceful shutdown (409 in dev mode)
- Extract dev startup to `backend/dev_server.py`

### 3B.4: `desktop_launcher.py` (depends on 3B.3)
PyInstaller entry point at repo root. Starts uvicorn with `app` object directly (not import string), polls for readiness, opens browser, handles already-running detection, shows MessageBox on failure.

### 3B.5: Enhance iCloud folder detection (no deps, standalone)
Add Windows registry lookup to `backend/config.py` before filesystem path fallback. Best-effort via `winreg`.

### 3B.6: Frontend "Exit App" button (depends on 3B.3)
- `types/api.ts`: `QuitAppResponse`
- `hooks/useApi.ts`: `quitApp()`
- `components/Settings.tsx`: "Exit App" button, handles 409 gracefully

### 3B.7: `icloud_sorter.spec` (depends on 3B.4)
PyInstaller spec file. Bundles `frontend/dist/`, hidden imports for uvicorn/pyicloud, certifi CA data. Also create `requirements-build.txt`.

### 3B.8: `scripts/build_windows.ps1` (depends on 3B.7)
Build script: frontend build → pip install → PyInstaller run.

### 3B.9: Test & iterate (depends on 3B.8)
Test `onedir` + `console=True` first to debug, then switch to `onefile` + `console=False` for release.

## Dependency Graph

```
3B.1 (runtime_paths) ─┐
3B.2 (lifecycle)      ─┼─→ 3B.3 (app.py) ─→ 3B.4 (launcher) ─→ 3B.7 (spec) ─→ 3B.8 (build script) ─→ 3B.9 (test)
                       │                  └─→ 3B.6 (frontend exit button)
3B.5 (registry detect) ── standalone
```

## New Files

| File | Purpose |
|------|---------|
| `backend/runtime_paths.py` | PyInstaller-safe path resolution |
| `backend/lifecycle.py` | Shutdown callback for desktop mode |
| `backend/dev_server.py` | Dev startup (replaces `__main__` in app.py) |
| `desktop_launcher.py` | PyInstaller entry point |
| `icloud_sorter.spec` | PyInstaller build spec |
| `requirements-build.txt` | Build-only dependencies |
| `scripts/build_windows.ps1` | Build automation |

## Modified Files

| File | Changes |
|------|---------|
| `backend/app.py` | Use runtime_paths, add health/quit endpoints, remove `__main__` |
| `backend/config.py` | Add registry-based iCloud folder detection |
| `frontend/src/types/api.ts` | Add `QuitAppResponse` |
| `frontend/src/hooks/useApi.ts` | Add `quitApp()` |
| `frontend/src/components/Settings.tsx` | Add "Exit App" button |

## Key Constraints & Gotchas

1. **uvicorn under PyInstaller**: Must use `app` object directly, NOT import string. `reload=False`, `workers=1`.
2. **TLS/certifi**: pyicloud needs CA certs. Bundle `certifi` data in spec or auth will fail.
3. **Frontend paths**: `sys._MEIPASS` changes the root. Must use `runtime_paths.frontend_dist()`.
4. **SQLite/cookies/settings**: Already stored in `~/.icloud-sorter/` (outside bundle) — no changes needed.
5. **Port conflicts**: If 8000 is taken and health check fails, show a clear error.
6. **One-file cold start**: `--onefile` extracts to temp on launch (~5-10s). Acceptable for Phase 3B.

## What's NOT in scope

- Tray icon (adds pystray + Pillow dependency, unnecessary for first release)
- Auto-updates (Phase 3C/3D territory)
- Installer/MSI (portable `.exe` is sufficient for MVP)
- macOS/Linux packaging (Windows-only for now)
- pywebview native window (browser-based is fine for Phase 3B)
