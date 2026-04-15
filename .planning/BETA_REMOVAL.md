# Beta Expiry — Removal Checklist

Remove all of this before the v1.0 release. Grep for `# BETA` to find inline markers.

## Files to delete
- `backend/beta.py`
- `scripts/stamp_beta.py`

## Files to edit

| File | What to remove |
|---|---|
| `backend/app.py` | `/api/app/beta` endpoint (~5 lines) |
| `scripts/build_windows.ps1` | Step 3: beta stamp (3 lines) |
| `frontend/src/types/api.ts` | `BetaStatusResponse` interface |
| `frontend/src/hooks/useApi.ts` | `getBetaStatus` function + `BetaStatusResponse` import |
| `frontend/src/App.tsx` | `betaStatus` state, `getBetaStatus` call in `init()`, `betaBanner` variable, expired screen, banner renders (2×) |
| `frontend/src/styles/index.css` | `.beta-banner` CSS block |
| `.gitignore` | `backend/_beta_stamp.py` line |
