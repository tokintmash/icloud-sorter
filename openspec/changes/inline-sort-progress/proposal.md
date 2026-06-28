## Why

Showing sort progress in a separate tab adds unnecessary navigation during the main sorting task and makes it less clear that progress belongs to the albums the user just selected. Keeping progress next to the album list and start action creates a simpler, more continuous sorting experience.

## What Changes

- Update the authenticated frontend flow so sort progress appears inline in the album selection view after sorting starts.
- Place the progress UI close to the start sorting action, including the progress bar, current file or album, error summary, and completion state.
- Remove the need for users to switch to a separate progress tab or screen to monitor a running sort.
- Preserve the existing backend sort start and SSE progress API contract.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `frontend-flow`: Sort progress presentation changes from a separate progress view to inline feedback within the album selection view.

## Impact

- Frontend routing/state in `frontend/src/App.tsx` may change so starting a sort no longer navigates to a separate progress screen.
- Album selection UI in `frontend/src/components/AlbumPicker.tsx` may render progress controls or embed the existing progress component near the sort button.
- Sort progress UI in `frontend/src/components/SortProgress.tsx` may be adjusted to support inline rendering while preserving displayed data.
- Frontend styles in `frontend/src/styles/index.css` may need layout updates.
- No backend API, database, or dependency changes are expected.
