# Phase 3B Fix Tracker

Based on `.planning/PHASE3B_REVIEW.md` findings.

## Fixes

| # | Severity | File | Description | Status |
|---|----------|------|-------------|--------|
| 1 | Critical | `backend/app.py` | Directory traversal in SPA fallback — add `.resolve()` + `.is_relative_to()` check | ⬜ TODO |
| 2 | High | `desktop_launcher.py` | `/api/app/quit` doesn't close pywebview window — register `window.destroy()` shutdown callback | ⬜ TODO |
| 3 | Medium | `icloud_sorter.spec` | Fragile `hiddenimports` — remove unnecessary `backend.*` entries | ⬜ TODO |
| 4 | Low | `icloud_sorter.spec` | `onedir` + `console=False` mismatch — mitigated by redirecting `sys.stdout`/`sys.stderr` to devnull in `desktop_launcher.py` | ✅ DONE |
| 5 | Low | `backend/config.py` | Registry key fallback — add `Software\Apple Inc.\Internet Services` lookup | ⬜ TODO |
| 6 | High | `icloud_sorter.spec` | Missing `fido2/public_suffix_list.dat` in PyInstaller bundle — add to `datas` | ✅ DONE |
| 7 | High | `scripts/build_windows.ps1` | Em-dash encoding issue | ✅ FIXED (pre-review) |
| 8 | High | `requirements-build.txt` | `pythonnet` incompatible with Python 3.14 | ✅ FIXED (pre-review) |
