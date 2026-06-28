## 1. Frontend Flow

- [x] 1.1 Load and apply the `ui-ux-pro-max` skill before editing UI code; inspect the current album picker, toolbar, progress, mobile behavior, focus states, and visual tokens.
- [x] 1.2 Remove the dedicated `sorting` tab from authenticated navigation and eliminate the empty sorting-tab placeholder state.
- [x] 1.3 Update sort start handling so clicking `Sort Selected` keeps the user on the albums tab and records the selected album IDs for inline progress.
- [x] 1.4 Ensure settings remains accessible without changing authentication, consent, expiry, or API error handling flows.

## 2. Inline Progress UI

- [x] 2.1 Render `SortProgress` from the album selection interface near the `Sort Selected` button when a sort request is active.
- [x] 2.2 Pass session-expiry and app-expiry callbacks through the inline progress path.
- [x] 2.3 Keep terminal completion or error results visible inline until the user dismisses them with the existing completion action.
- [x] 2.4 Prevent duplicate or conflicting sort starts while inline progress is starting, running, or awaiting dismissal.

## 3. Styling And Verification

- [x] 3.1 Adjust CSS so inline progress appears as a clear full-width section or card near the album toolbar on desktop and mobile.
- [x] 3.2 Use the `ui-ux-pro-max` checklist to verify hierarchy, one clear primary action, responsive behavior at mobile and desktop widths, keyboard/focus behavior, disabled/loading/error states, and contrast within the existing design system.
- [x] 3.3 Verify album selection, sort start, progress updates, terminal completion, error display, settings navigation, and expiry/session handling still behave correctly.
- [x] 3.4 Run `cd frontend && npm run build` and fix any TypeScript or build failures.
