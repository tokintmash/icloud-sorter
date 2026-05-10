## Context

The frontend currently initializes beta status and session state in `App.tsx`, then routes unauthenticated users directly to `AuthScreen`. The sorter reads iCloud Photos metadata after authentication and moves locally synced files during sorting, so users need a clear pre-authentication explanation of those access needs before entering Apple ID credentials.

## Goals / Non-Goals

**Goals:**
- Show a consent screen before the login form for first-time use on a device/browser.
- Clearly describe the data involved: iCloud Photos album metadata, filenames, album membership, and local iCloud Photos folder file access.
- Clearly state that the app does not download images/videos from iCloud and does not upload files or data from the computer.
- Clearly state that Apple ID credentials are used only to authenticate with Apple and are not stored by the app.
- Require an explicit user action before continuing to authentication.
- Remember accepted consent locally so returning users do not see the screen on every app load.
- Preserve existing beta-expired blocking behavior and authenticated session handling.

**Non-Goals:**
- Add backend consent storage, audit logging, or a new API endpoint.
- Change iCloud authentication, album fetching, sorting behavior, or local file permissions.
- Provide legal terms, privacy policy hosting, or consent revocation workflows beyond local browser state.
- Implement custom credential storage or credential proxying.

## Decisions

- Gate only unauthenticated login behind consent. If an existing backend session is already authenticated, the app continues directly to the authenticated UI because the user has already completed the access flow on that session.
- Store consent in `localStorage` using a versioned key. This keeps the feature frontend-only and allows future wording changes to require renewed consent by changing the key.
- Implement a small dedicated `ConsentScreen` component instead of folding text into `AuthScreen`. This keeps authentication concerns separate from pre-auth disclosure and makes the routing state explicit in `App.tsx`.
- Use existing card, button, and typography styling with a few targeted consent classes. This preserves the current design system and avoids introducing a UI dependency.
- Do not block beta-expired users with the consent screen. Expired builds should continue to show the beta expiration message before any other app flow.

## Risks / Trade-offs

- Local-only consent can be cleared by browser storage cleanup -> the user will be asked again, which is safe and does not affect backend state.
- Local-only consent is not a durable compliance audit trail -> acceptable for this MVP because no backend persistence is required by the requested change.
- Copy may become inaccurate if backend data access changes later -> use a versioned storage key so future copy changes can force re-consent.
- Users with an already-authenticated session may not see the new consent screen immediately -> acceptable because gating existing sessions could interrupt current use; future implementation can force consent for all sessions if required.
