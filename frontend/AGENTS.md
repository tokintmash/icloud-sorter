# Frontend — Agent Instructions

## Scope

Everything under `frontend/`. Key files:

- `package.json`, `tsconfig.json`, `vite.config.ts`
- `index.html`
- `src/App.tsx` — Root component, auth state machine, tab navigation
- `src/components/` — `AuthScreen.tsx`, `AlbumBrowser.tsx`, `DownloadProgress.tsx`, `Settings.tsx`
- `src/hooks/useApi.ts` — API client functions
- `src/types/api.ts` — TypeScript types matching backend Pydantic schemas
- `src/styles/`

---

## Constraints

- React + TypeScript, scaffolded with Vite
- TypeScript types in `types/api.ts` must match the API contract in root `AGENTS.md` exactly
- TypeScript strict mode, no `any` types
- API calls go to `/api/*` (proxy to `http://localhost:8000` in dev via Vite config)
- SSE via `EventSource` for download progress — match the SSE Progress Schema in root `AGENTS.md`; handle reconnection (server sends full snapshot)
- Handle `session_expired` SSE status by redirecting user to re-authenticate
- Production build outputs to `frontend/dist/` which FastAPI serves as static files
- No external UI framework required — keep it simple (plain CSS or minimal library)
- Handle error responses using the standard error shape: `{ error, message }`

---

## Auth Flow State Machine

```
unauthenticated → awaiting_2fa → authenticated
                                   ↓
                              session_expired → unauthenticated
```

---

## UI Requirements

- **AlbumBrowser:** List albums with checkboxes, expandable asset tables with per-file checkboxes (see `PLANNING_FILE_SELECTION.md`), "Download Selected" button
- **DownloadProgress:** Overall progress bar, speed, ETA, per-file error list with retry count
- **Settings:** Expose `download_path`, `concurrent_downloads` (1–10), `metadata_delay_ms`, `max_retries`

---

## Testing

- `npm run build` succeeds with zero TypeScript errors
- Dev server starts with `npm run dev`
