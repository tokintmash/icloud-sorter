# Phase 3B: Desktop Packaging — Implementation Plan

## Decision: PyInstaller (not Electron)

The app already serves the React frontend from FastAPI. Electron would add a second runtime, IPC complexity, and ~100MB+ bundle size for zero benefit. PyInstaller bundles everything into a single `.exe` that opens the user's browser.

## Architecture

```
User double-clicks iCloudPhotoSorter.exe
  → desktop_launcher.py (PyInstaller entry point)
    → Start uvicorn server (background thread, reload=False)
    → Poll /api/app/health every 250ms
    → When ready: open pywebview window → http://127.0.0.1:8000
    → On window close: server.should_exit = True → process exits
```

Uses **pywebview** for a native app window (uses OS WebView2 on Windows, no bundled Chromium). No browser tabs, no port-conflict UX issues.

## Tasks (in dependency order)

### 3B.1: `backend/runtime_paths.py` (no deps)
PyInstaller-safe path resolution. `bundle_root()` returns `sys._MEIPASS` when frozen, project root in dev. `frontend_dist()` returns the frontend build directory.

### 3B.2: `backend/lifecycle.py` (no deps)
Shutdown callback system. `register_shutdown_callback()` / `can_shutdown()` / `request_shutdown()`. Desktop launcher registers a callback; dev mode has none registered.

### 3B.3: Update `backend/app.py` (depends on 3B.1, 3B.2)
- Use `runtime_paths.frontend_dist()` for static files
- Add `GET /api/app/health` → `{"ok": true}`
- Add `POST /api/app/quit` → graceful shutdown (409 in dev mode)
- Extract dev startup logic to `backend/dev_server.py`
- Keep `__main__` block in `app.py` that calls `dev_server.run()` — `python backend/app.py` must still work

### 3B.4: `desktop_launcher.py` (depends on 3B.3)
PyInstaller entry point at repo root. Starts uvicorn with `app` object directly (not import string) in a background thread, polls `/api/app/health` for readiness, then opens a **pywebview** native window pointing to `http://127.0.0.1:8000`. On window close, sets `server.should_exit = True` and exits. Shows MessageBox on startup failure.

### 3B.5: Enhance iCloud folder detection (no deps, standalone)
Add Windows registry lookup to `backend/config.py` before filesystem path fallback. Best-effort via `winreg`.

### 3B.6: Frontend cleanup (depends on 3B.3)
No "Exit App" button needed — closing the pywebview window shuts everything down. This task is reserved for any minor frontend adjustments needed for the desktop context (e.g., hiding browser-only UI if any).

### 3B.7: `icloud_sorter.spec` (depends on 3B.4)
PyInstaller spec file. Bundles `frontend/dist/`, hidden imports for uvicorn/pyicloud/pywebview, certifi CA data. Also create `requirements-build.txt` (includes `pywebview`).

### 3B.8: `scripts/build_windows.ps1` (depends on 3B.7)
Build script: frontend build → pip install → PyInstaller run.

### 3B.9: Test & iterate (depends on 3B.8)
Test `onedir` + `console=True` first to debug, then switch to `onefile` + `console=False` for release.

### 3B.10: Tests & README (depends on 3B.9)
- Add/update tests for new modules: `runtime_paths.py`, `lifecycle.py`, health/quit endpoints, registry-based folder detection
- Update `README.md` with: build instructions, how to run the `.exe`, system requirements (Windows 10/11, WebView2)
- Run full test suite (`pytest` + `npm run build`) and fix any failures before marking phase complete

## Dependency Graph

```
3B.1 (runtime_paths) ─┐
3B.2 (lifecycle)      ─┼─→ 3B.3 (app.py) ─→ 3B.4 (launcher) ─→ 3B.7 (spec) ─→ 3B.8 (build script) ─→ 3B.9 (test) ─→ 3B.10 (tests & README)
                       │                  └─→ 3B.6 (frontend cleanup)
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

## Key Constraints & Gotchas

1. **uvicorn under PyInstaller**: Must use `app` object directly, NOT import string. `reload=False`, `workers=1`.
2. **TLS/certifi**: pyicloud needs CA certs. Bundle `certifi` data in spec or auth will fail.
3. **Frontend paths**: `sys._MEIPASS` changes the root. Must use `runtime_paths.frontend_dist()`.
4. **SQLite/cookies/settings**: Already stored in `~/.icloud-sorter/` (outside bundle) — no changes needed.
5. **Port conflicts**: If 8000 is taken, uvicorn will fail to bind. Launcher catches this and shows a MessageBox error.
6. **One-file cold start**: `--onefile` extracts to temp on launch (~5-10s). Acceptable for Phase 3B.
7. **pywebview + WebView2**: Windows 10/11 ships with WebView2. No extra runtime needed. pywebview uses it automatically.

## What's NOT in scope

- Tray icon (adds pystray + Pillow dependency, unnecessary for first release)
- Auto-updates (Phase 3C/3D territory)
- Installer/MSI (portable `.exe` is sufficient for MVP)
- macOS/Linux packaging (Windows-only for now)
- Multi-instance prevention (if user double-clicks twice, two windows open — acceptable for MVP)
