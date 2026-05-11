## Context

The project already has a PyInstaller `onedir` spec (`icloud_sorter.spec`) that bundles `desktop_launcher.py`, the FastAPI backend, pywebview, and `frontend/dist`. The packaged app starts a local uvicorn server and opens a native pywebview window against `http://127.0.0.1:8000`.

Runtime mutable state is already separated from application files: SQLite state, settings, and cookies live under `Path.home() / ".icloud-sorter"`, while photo files live in a user-selected iCloud Photos folder. That separation is the main constraint that makes a future MSIX package plausible.

The MSI layer should therefore be a thin Windows installer around the PyInstaller output, not a second runtime configuration system.

```text
frontend build
   │
   ▼
PyInstaller onedir bundle
   │
   ▼
MSI authoring tool
   │
   ▼
installed app files          user data                user photos
read-only/replaceable        writable                 external
```

## Goals / Non-Goals

**Goals:**

- Produce an MSI installer for the Windows desktop app from the existing frontend build and PyInstaller `onedir` bundle.
- Keep runtime behavior independent from MSI-specific install paths, registry writes, or custom actions.
- Preserve an MSIX-friendly split between immutable installed files and mutable user data.
- Provide deterministic packaging commands and verification steps for install, launch, uninstall, and user-data preservation.

**Non-Goals:**

- Produce an MSIX package in this change.
- Add auto-update behavior.
- Add Microsoft Store packaging.
- Change auth, album listing, sorting, settings APIs, or frontend flow.
- Move user data into the installer-managed application directory.

## Decisions

### Use PyInstaller `onedir` as the MSI payload

The MSI will package the collected `dist/iCloudPhotoSorter/` directory instead of a PyInstaller `onefile` executable.

Rationale: `onedir` makes the installed layout explicit, avoids per-launch extraction behavior, and resembles the immutable package layout expected by MSIX. It also keeps bundled frontend assets visible to the existing `backend.runtime_paths.frontend_dist()` logic.

Alternatives considered:

- `onefile`: simpler to distribute as a standalone executable, but less installer-friendly, has extraction/startup trade-offs, and is a weaker model for future MSIX packaging.
- Native Python environment install: unsuitable for non-developer users and undermines the goal of a self-contained desktop app.

### Use a declarative MSI authoring tool

The implementation should prefer a declarative MSI authoring tool such as WiX Toolset over imperative installer scripting.

Rationale: a declarative installer keeps behavior inspectable and limits the temptation to add custom actions that would not translate to MSIX. The MSI should mostly install files, create shortcuts, and register uninstall metadata.

Alternatives considered:

- Inno Setup or NSIS: simpler for many desktop apps, but they do not produce MSI and can encourage script-heavy install behavior.
- Advanced Installer: viable, especially with a GUI, but less ideal as the default project artifact if reproducible source-controlled configuration is the priority.

### Keep installer behavior minimal

The MSI should avoid machine-wide side effects unless they become explicit requirements later.

The installer should not require:

- PATH mutation.
- Windows service registration.
- Shell extensions.
- Drivers.
- Installer-time authentication.
- Installer-time iCloud folder detection.
- Runtime configuration written beside the executable.

Rationale: these constraints keep the MSI close to MSIX's package model and reduce install/uninstall risk.

### Preserve user data on uninstall

Uninstalling the MSI should remove installed application files and shortcuts, but not delete `~/.icloud-sorter` or user photo files.

Rationale: uninstall should not destroy app state, cookies, settings, sort history, or user-managed photos. This also mirrors modern package behavior where user data is separate from app binaries.

Alternative considered:

- Remove all app state on uninstall: surprising and potentially destructive. If a future cleanup option is wanted, it should be explicit and user-confirmed, not default MSI behavior.

### Treat code signing as a packaging concern, not a runtime dependency

The MSI plan should allow unsigned local development builds, but document that release installers should be signed.

Rationale: MSIX requires signing, and signed MSI builds reduce SmartScreen friction. However, requiring signing for every local packaging test would slow development.

## Risks / Trade-offs

- [Risk] PyInstaller output may include files that change between builds and make MSI component identity unstable. -> Mitigation: define a repeatable harvest/build step and keep generated installer artifacts out of hand-edited source where practical.
- [Risk] The app currently binds to fixed port `8000`; an installed desktop app can fail if another local process uses that port. -> Mitigation: keep this visible as packaging verification risk; defer runtime port changes unless packaging tests show it blocks installed usage.
- [Risk] Windows Defender or SmartScreen may warn on unsigned PyInstaller/MSI outputs. -> Mitigation: support unsigned developer builds but document signing as required for release distribution and future MSIX.
- [Risk] pywebview/pythonnet dependencies may have native runtime requirements not present on a clean Windows machine. -> Mitigation: verify the MSI on a clean Windows environment and add prerequisites only when proven necessary.
- [Risk] MSI custom actions can solve short-term issues but make MSIX migration harder. -> Mitigation: require any custom action to be justified in design/tasks before implementation.

## Migration Plan

1. Keep the current developer flow unchanged.
2. Add a packaging flow that builds the frontend, builds the PyInstaller `onedir` bundle, then creates the MSI.
3. Verify the installed app launches and serves the bundled frontend from the installed location.
4. Verify uninstall removes installed files and shortcuts while preserving `~/.icloud-sorter` and user photo files.
5. Future MSIX work can reuse the PyInstaller `onedir` payload and user-data separation, replacing the MSI authoring layer with an MSIX manifest/package layer.

Rollback strategy: removing the MSI packaging configuration/scripts returns the project to the current PyInstaller-only packaging state without changing runtime app behavior.

## Open Questions

- Should the first MSI default to per-user install, per-machine install, or support both?
- What product name, manufacturer, upgrade code, icon, and versioning source should the MSI use?
- Will release distribution require Authenticode signing immediately, or only after the MSI flow works locally?
