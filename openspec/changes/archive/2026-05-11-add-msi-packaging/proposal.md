## Why

The app needs a distributable Windows installer so users can install and launch it without running Python, Node, or development commands. MSI is the practical first packaging target, but the installer should avoid assumptions that would make a later MSIX package difficult.

## What Changes

- Add a Windows desktop packaging capability for producing an MSI installer from the existing built frontend and PyInstaller application bundle.
- Define packaging constraints that keep installed application files immutable and store mutable state in user-writable profile locations.
- Add installer verification expectations for install, launch, uninstall, and preservation of user data.
- Do not change runtime API contracts, authentication behavior, album metadata behavior, sorting behavior, or frontend flow.
- Do not introduce MSIX packaging in this change; preserve compatibility with a future MSIX-oriented package by avoiding MSI-only runtime assumptions.

## Capabilities

### New Capabilities

- `desktop-packaging`: Windows desktop packaging, installer behavior, installed-file layout, user-data separation, and MSIX-friendly packaging constraints.

### Modified Capabilities

- None.

## Impact

- Adds build/package scripts or configuration for creating an MSI installer around the PyInstaller output.
- May add or document packaging dependencies such as PyInstaller and an MSI authoring tool.
- May adjust application path handling only if needed to make bundled/static assets load correctly from an installed location.
- Requires verification on Windows for install, launch, API/frontend serving, uninstall, and user-data preservation.
