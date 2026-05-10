## Why

Users should understand and explicitly consent to the data access required before signing in or configuring the sorter. This improves transparency around iCloud Photos metadata access and local file access before the app performs any photo organization work.

## What Changes

- Add an opening consent screen shown before the authentication flow.
- Explain that the app reads iCloud Photos metadata such as album names, asset filenames, and album membership.
- Explain that the app needs access to the local iCloud Photos folder to find and move files into album folders.
- Explain that the app does not download images or videos from iCloud and does not upload anything from the computer.
- Explain that Apple ID credentials are used only for Apple/iCloud authentication through the app's local backend authentication flow and are not stored by the app.
- Require the user to accept the consent statement before continuing to Apple ID login.
- Keep consent local to the app; no new backend API or external dependency is introduced.

## Capabilities

### New Capabilities
- `data-access-consent`: Covers the pre-authentication consent experience for iCloud Photos metadata and local file access.

### Modified Capabilities
- `frontend-flow`: The unauthenticated entry flow now shows consent before the authentication screen when current local consent has not been accepted.

## Impact

- Affects frontend screen routing and auth entry flow in `frontend/src/App.tsx`.
- Adds or updates a frontend component for the consent screen.
- May add local browser storage for remembering the user's consent on the same device.
- No backend API, database schema, or dependency changes are expected.
