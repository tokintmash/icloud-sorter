## 1. Consent UI

- [ ] 1.1 Add a `ConsentScreen` React component that explains iCloud Photos metadata access, local iCloud Photos folder access, no image/video downloads from iCloud, no uploads from the computer, and Apple ID credential handling.
- [ ] 1.2 Add consent screen styling in `frontend/src/styles/index.css` using the existing card, typography, and button design language.

## 2. App Flow

- [ ] 2.1 Add a versioned local consent storage key and read it during frontend app initialization.
- [ ] 2.2 Route unauthenticated users without current consent to `ConsentScreen` before `AuthScreen`.
- [ ] 2.3 Persist consent locally when the user accepts and then continue to the Apple ID login flow.
- [ ] 2.4 Preserve beta-expired rendering and authenticated-session routing behavior.

## 3. Verification

- [ ] 3.1 Verify a new unauthenticated browser state shows consent before login.
- [ ] 3.2 Verify accepted consent is remembered locally and login appears directly on a later unauthenticated app load.
- [ ] 3.3 Run `cd frontend && npm run build` and fix any TypeScript or build errors.
