## Context

The authenticated frontend currently exposes separate `albums`, `sorting`, and `settings` tabs. Starting a sort from `AlbumPicker` stores the selected album IDs in `App`, switches the active tab to `sorting`, and mounts `SortProgress`, which calls `POST /api/sort/start` and then listens to `/api/sort/progress` with `EventSource`.

The change is purely frontend presentation. The backend sort start endpoint, SSE stream, progress event shape, settings, authentication, and persisted state remain unchanged.

## Goals / Non-Goals

**Goals:**

- Keep users on the album selection view after they click `Sort Selected`.
- Show the existing sort progress information inline near the sort action: starting state, progress bar, current file or album, failures, terminal status, and completion action.
- Preserve session-expiry and app-expiry handling already performed by the sort progress flow.
- Preserve the existing settings access pattern as a separate authenticated area.

**Non-Goals:**

- Changing backend API contracts or SSE behavior.
- Adding persistent sort history or resumable sorting.
- Redesigning album fetching, selection, or settings beyond what is needed for inline progress.
- Introducing a new routing library or external UI framework.

## Decisions

- Render progress from the album view instead of using a dedicated `sorting` tab.
  - Rationale: The progress belongs to the selected albums and the action that started it. Keeping it visible next to the start button removes a navigation step and avoids an empty sorting tab when no sort is active.
  - Alternative considered: Keep the tab but auto-switch back on completion. This still leaves users with two places for one task and does not solve the UX confusion.

- Reuse `SortProgress` for sort initiation and SSE handling.
  - Rationale: `SortProgress` already owns `startSort`, EventSource lifecycle, terminal handling, error display, and expiry/session callbacks. Reusing it minimizes behavior changes and reduces risk.
  - Alternative considered: Move start/progress logic directly into `AlbumPicker`. That would couple album list state to SSE lifecycle details and duplicate error-handling paths.

- Let `AlbumPicker` own the current selected sort request while it is rendering the album screen.
  - Rationale: The album screen can pass selected album IDs to `SortProgress` and clear them when the user acknowledges completion. `App` no longer needs to maintain an `activeTab === 'sorting'` route for normal progress display.
  - Alternative considered: Keep `sortState` in `App` and pass it down to `AlbumPicker`. This is viable but less direct unless a running sort must survive navigation away from the album view.

- Disable or de-emphasize conflicting album actions while a sort is starting or running.
  - Rationale: Refreshing albums or starting another sort during an active sort can confuse the displayed progress and backend state. The UI should make the active operation clear.
  - Alternative considered: Allow all controls and rely on backend `sort_in_progress` errors. That produces avoidable error states for users.

- Apply the `ui-ux-pro-max` skill during implementation.
  - Rationale: This change directly affects the user's main task flow and visual hierarchy. The skill's discipline should be used to inspect the existing UI, keep the established design language, ensure one clear primary action, and cover responsive, accessible interaction states.
  - Alternative considered: Treat the change as a mechanical component move. That would risk preserving the current confusion in a different layout instead of deliberately improving the experience.

## Risks / Trade-offs

- Running sort state can be unmounted if the user navigates to settings while sorting -> Keep settings accessible, but ensure returning to albums does not accidentally start a second sort; if preserving live progress across settings navigation is required, keep active sort state in `App` and render progress only on the albums tab.
- `SortProgress` currently calls `startSort` on mount -> Ensure inline rendering mounts it exactly once per user sort request to avoid duplicate start requests.
- Removing the sorting tab changes navigation expectations -> Keep completion feedback and a clear `Done` action inline so users know the operation reached a terminal state.
- Inline progress may crowd the album toolbar on small screens -> Style progress as a full-width card below or adjacent to the toolbar, with responsive stacking.
- UI polish may expand scope beyond the requested flow change -> Use `ui-ux-pro-max` only to improve the inline progress integration within existing patterns, not to redesign unrelated screens.
