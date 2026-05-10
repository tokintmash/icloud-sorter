## 1. Consent UI

- [x] 1.1 Add a `ConsentScreen` React component that explains iCloud Photos metadata access, local iCloud Photos folder access, no image/video downloads from iCloud, no uploads from the computer, and Apple ID credential handling.
- [x] 1.2 Add consent screen styling in `frontend/src/styles/index.css` using the existing card, typography, and button design language.

## 2. App Flow

- [x] 2.1 Add a versioned local consent storage key and read it during frontend app initialization.
- [x] 2.2 Route unauthenticated users without current consent to `ConsentScreen` before `AuthScreen`.
- [x] 2.3 Persist consent locally when the user accepts and then continue to the Apple ID login flow.
- [x] 2.4 Preserve beta-expired rendering and authenticated-session routing behavior.

## 3. Verification

- [x] 3.1 Verify a new unauthenticated browser state shows consent before login.
- [x] 3.2 Verify accepted consent is remembered locally and login appears directly on a later unauthenticated app load.
- [x] 3.3 Run `cd frontend && npm run build` and fix any TypeScript or build errors.

## 4. Sonar Follow-up

- [x] 4.1 Replace consent-flow `window.localStorage` references in `frontend/src/App.tsx` and `frontend/src/App.test.tsx` with `globalThis.localStorage` to resolve Sonar `typescript:S7764` findings introduced by this change.
- [x] 4.2 Re-run frontend verification after the Sonar cleanup.
